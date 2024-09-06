import os
import json
from typesense import Client
import logging
from tqdm import tqdm

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Typesense client configuration
client = Client({
    'nodes': [{
        'host': 'localhost',
        'port': '8108',
        'protocol': 'http'
    }],
    'api_key': 'xyz',
    'connection_timeout_seconds': 2
})

# Schema definition
schema = {
    'name': 'typesense_docs',
    'fields': [
        {'name': 'id', 'type': 'string', 'facet': False, 'index': True, 'sort': True},  # Add 'sort': True
        {'name': 'content', 'type': 'string'},
        {'name': 'source', 'type': 'string'},
    ]
}

def create_collection():
    try:
        client.collections.create(schema)
        logger.info("Collection 'typesense_docs' created successfully.")
    except Exception as e:
        if 'already exists' in str(e):
            logger.info("Collection 'typesense_docs' already exists.")
        else:
            logger.error(f"Error creating collection: {e}")
            raise

def delete_collection():
    try:
        client.collections['typesense_docs'].delete()
        logger.info("Collection 'typesense_docs' deleted successfully.")
    except Exception as e:
        logger.warning(f"Error deleting collection: {e}")

def insert_documents(data_file):
    try:
        with open(data_file, 'r') as f:
            documents = json.load(f)
        
        with tqdm(total=len(documents), desc="Inserting documents") as pbar:
            for doc in documents:
                document = {
                    'id': doc['id'],
                    'content': doc['content'],
                    'source': doc['metadata']['source']
                }
                client.collections['typesense_docs'].documents.upsert(document)
                pbar.update(1)
        logger.info(f"Successfully inserted {len(documents)} documents.")
    except Exception as e:
        logger.error(f"Error inserting documents: {e}")
        raise

def query_documents():
    try:
        search_parameters = {
            'q': '*',
            'query_by': 'content',
            'limit': 5
        }
        results = client.collections['typesense_docs'].documents.search(search_parameters)
        logger.info(f"Query results: {json.dumps(results, indent=2)}")
    except Exception as e:
        logger.error(f"Error querying documents: {e}")
        raise

if __name__ == "__main__":
    data_file = 'data_raw/typesense_docs_chunks.json'
    
    delete_collection()  # Add this line
    create_collection()
    insert_documents(data_file)
    query_documents()
