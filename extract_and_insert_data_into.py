import os
from dotenv import load_dotenv
import typesense
import requests
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Typesense client setup
node = {
    "host": "localhost",
    "port": "8108",
    "protocol": "http"
}
typesense_client = typesense.Client(
    {
      "nodes": [node],
      "api_key": os.getenv('TYPESENSE_API_KEY'),
      "connection_timeout_seconds": 2
    }
)
collection_name = "ai_related_discussions"

# GitHub API details
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}

def chunk_text(text, chunk_size=200):
    words = text.split()
    return [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

def fetch_discussions(owner, repo):
    query = """
    query($cursor: String) {
      repository(owner: "%s", name: "%s") {
        discussions(first: 100, after: $cursor, orderBy: {field: CREATED_AT, direction: DESC}) {
          pageInfo {
            endCursor
            hasNextPage
          }
          edges {
            node {
              title
              bodyText
              createdAt
              url
              author {
                login
              }
              comments(first: 5) {
                edges {
                  node {
                    bodyText
                    author {
                      login
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    """ % (owner, repo)

    variables = {
        "cursor": None
    }

    discussions = []

    while True:
        response = requests.post(
            'https://api.github.com/graphql',
            headers=HEADERS,
            json={'query': query, 'variables': variables}
        )

        if response.status_code != 200:
            raise Exception(f"Query failed to run by returning code of {response.status_code}. {response.text}")

        response_json = response.json()
        if 'errors' in response_json:
            raise Exception(f"GraphQL query error: {response_json['errors']}")

        if 'data' not in response_json or 'repository' not in response_json['data'] or 'discussions' not in response_json['data']['repository']:
            raise Exception(f"Unexpected response format: {response_json}")

        data = response_json['data']['repository']['discussions']
        discussions.extend([edge['node'] for edge in data['edges']])

        if not data['pageInfo']['hasNextPage']:
            break

        variables['cursor'] = data['pageInfo']['endCursor']

    return discussions

def create_collection_if_not_exists(collection_name):
    schema = {
        'name': collection_name,
        'fields': [
            {'name': 'repository', 'type': 'string'},
            {'name': 'title', 'type': 'string'},
            {'name': 'bodyText', 'type': 'string'},
            {'name': 'createdAt', 'type': 'string'},
            {'name': 'url', 'type': 'string'},
            {'name': 'author', 'type': 'string'},
            {'name': 'comments', 'type': 'string[]'}
        ]
    }

    try:
        typesense_client.collections[collection_name].retrieve()
        print(f"Collection '{collection_name}' already exists.")
    except typesense.exceptions.ObjectNotFound:
        typesense_client.collections.create(schema)
        print(f"Collection '{collection_name}' created.")

def insert_into_typesense(collection_name, discussions, repo_info):
    create_collection_if_not_exists(collection_name)

    for discussion in discussions:
        chunks = chunk_text(discussion['bodyText'])
        for chunk in chunks:
            document_id = f"{repo_info['owner']}_{repo_info['repo']}_{discussion['createdAt']}_{chunk[:50]}"
            document = {
                'id': document_id,
                'repository': f"{repo_info['owner']}/{repo_info['repo']}",
                'title': discussion['title'],
                'bodyText': chunk,
                'createdAt': discussion['createdAt'],
                'url': discussion['url'],
                'author': discussion['author']['login'],
                'comments': [comment['node']['bodyText'] for comment in discussion['comments']['edges']]
            }
            typesense_client.collections[collection_name].documents.upsert(document)

def verify_data_insertion(collection_name):
    try:
        documents = typesense_client.collections[collection_name].documents.search({
            'q': '*',
            'query_by': 'repository'
        })
        if documents['found'] > 0:
            print(f"Data successfully inserted into the collection '{collection_name}'. Total documents: {documents['found']}")
        else:
            print(f"No data found in the collection '{collection_name}'.")
    except Exception as e:
        print(f"Error verifying data insertion: {e}")

def print_sample_documents(collection_name, sample_size=5):
    try:
        documents = typesense_client.collections[collection_name].documents.search({
            'q': '*',
            'query_by': 'repository',
            'per_page': sample_size
        })
        print(f"Sample documents from the collection '{collection_name}':")
        for document in documents['hits']:
            print(document['document'])
    except Exception as e:
        print(f"Error fetching sample documents: {e}")

# Main function
if __name__ == "__main__":
    collection_name = "ai_related_discussions"  
    repositories = [
        {"owner": "keras-team", "repo": "keras"},
        {"owner": "explosion", "repo": "spacy"},
        {"owner": "allenai", "repo": "allennlp"},
        {"owner": "crewAIInc", "repo": "crewAI"}
    ]

    for repo_info in repositories:
        try:
            print(f"Fetching discussions for {repo_info['owner']}/{repo_info['repo']}...")
            discussions = fetch_discussions(repo_info['owner'], repo_info['repo'])
            if discussions:
                print(f"Fetched {len(discussions)} discussions. Inserting into Typesense...")
                insert_into_typesense(collection_name, discussions, repo_info)
            else:
                print(f"No discussions found for {repo_info['owner']}/{repo_info['repo']}. Skipping...")
        except Exception as e:
            print(f"Error fetching discussions for {repo_info['owner']}/{repo_info['repo']}: {e}")

    verify_data_insertion(collection_name)
    print_sample_documents(collection_name)
    print("All discussions have been processed.")
