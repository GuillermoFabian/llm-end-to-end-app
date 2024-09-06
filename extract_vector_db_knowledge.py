import os
import typesense
import requests
import logging
import pandas as pd


if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test


GITHUB_TOKEN = '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'
TYPESENSE_API_KEY = 'xyz'

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


TYPESENSE_HOST = os.getenv('TYPESENSE_HOST', 'typesense')
TYPESENSE_PORT = os.getenv('TYPESENSE_PORT', '8108')
TYPESENSE_API_KEY = os.getenv('TYPESENSE_API_KEY', 'xyz')

logger.debug(f"Typesense configuration: Host={TYPESENSE_HOST}, Port={TYPESENSE_PORT}")

try:
    typesense_ip = socket.gethostbyname(TYPESENSE_HOST)
    logger.debug(f"Resolved Typesense IP: {typesense_ip}")
except socket.gaierror as e:
    logger.error(f"Failed to resolve Typesense hostname: {e}")
    typesense_ip = TYPESENSE_HOST  # Fall back to the original hostname if resolution fails

# Typesense client setup
node = {
    "host": "localhost",
    "port": "8108",
    "protocol": "http"
}
typesense_client = typesense.Client(
    {
      "nodes": [node],
      "api_key": TYPESENSE_API_KEY,
      "connection_timeout_seconds": 2
    }
)
collection_name = "ai_related_discussions"

# GitHub API details
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
        logger.info(f"Collection '{collection_name}' already exists.")
    except typesense.exceptions.ObjectNotFound:
        typesense_client.collections.create(schema)
        logger.info(f"Collection '{collection_name}' created.")

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

@data_loader
def load_github_discussions(*args, **kwargs):
    """
    Load GitHub discussions data into Typesense and return a summary DataFrame.
    """
    repositories = [
        {"owner": "keras-team", "repo": "keras"},
        {"owner": "explosion", "repo": "spacy"},
        {"owner": "allenai", "repo": "allennlp"},
        {"owner": "crewAIInc", "repo": "crewAI"}
    ]

    summary_data = []

    for repo_info in repositories:
        try:
            logger.info(f"Fetching discussions for {repo_info['owner']}/{repo_info['repo']}...")
            discussions = fetch_discussions(repo_info['owner'], repo_info['repo'])
            if discussions:
                logger.info(f"Fetched {len(discussions)} discussions. Inserting into Typesense...")
                insert_into_typesense(collection_name, discussions, repo_info)
                summary_data.append({
                    'repository': f"{repo_info['owner']}/{repo_info['repo']}",
                    'discussions_count': len(discussions)
                })
            else:
                logger.info(f"No discussions found for {repo_info['owner']}/{repo_info['repo']}. Skipping...")
        except Exception as e:
            logger.error(f"Error fetching discussions for {repo_info['owner']}/{repo_info['repo']}: {e}")

    return pd.DataFrame(summary_data)

@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, 'The output is undefined'
    assert isinstance(output, pd.DataFrame), 'The output is not a pandas DataFrame'
    assert 'repository' in output.columns, 'The output does not contain a repository column'
    assert 'discussions_count' in output.columns, 'The output does not contain a discussions_count column'
    assert len(output) > 0, 'The output DataFrame is empty'
