import os
from dotenv import load_dotenv
import typesense
from langchain_community.llms import OpenAI
from langchain.prompts import PromptTemplate
import streamlit as st
import logging
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import tiktoken

# Load environment variables from .env file
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

# Database setup
DB_USER = os.getenv('POSTGRES_USER', 'llm_logging_user')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'llm_logging_password')
DB_HOST = os.getenv('POSTGRES_HOST', 'host.docker.internal')  
DB_PORT = os.getenv('POSTGRES_PORT', '5433')
DB_NAME = os.getenv('POSTGRES_DB', 'llm_logging_db')

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class LLMResponse(Base):
    __tablename__ = 'llm_responses'

    id = Column(Integer, primary_key=True)
    query = Column(String)
    response = Column(String)
    rating = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

def calculate_precision_recall_f1(retrieved_docs, relevant_docs):
    retrieved_set = set(retrieved_docs)
    relevant_set = set(relevant_docs)

    true_positives = len(retrieved_set & relevant_set)
    false_positives = len(retrieved_set - relevant_set)
    false_negatives = len(relevant_set - retrieved_set)

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return precision, recall, f1_score

def search_typesense(query: str, relevant_docs: list, k: int = 10, num_typos: int = 2):
    search_parameters = {
        'q': query,
        'query_by': 'title,bodyText,comments',
        'num_typos': num_typos,
        'per_page': k
    }
    
    results = typesense_client.collections[collection_name].documents.search(search_parameters)
    
    retrieved_docs = [hit['document']['id'] for hit in results['hits']]
    precision, recall, f1_score = calculate_precision_recall_f1(retrieved_docs, relevant_docs)
    
    logger.info(f"Precision: {precision}, Recall: {recall}, F1 Score: {f1_score}")
    
    return results, precision, recall, f1_score

def num_tokens_from_string(string: str, encoding_name: str = "cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def extract_content_for_llm(search_results, max_tokens=3000):
    contexts = []
    total_tokens = 0
    for hit in search_results['hits']:
        title = hit['document'].get('title', '')
        body = hit['document'].get('bodyText', '')
        comments = hit['document'].get('comments', [])
        
        content = f"Title: {title}\n\nBody: {body}\n\nComments: {' | '.join(comments)}"
        content_tokens = num_tokens_from_string(content)
        
        if total_tokens + content_tokens > max_tokens:
            break
        
        contexts.append(content)
        total_tokens += content_tokens
    
    combined_context = "\n\n---\n\n".join(contexts)
    return combined_context

def log_response(query, response, rating, precision, recall, f1_score):
    session = Session()
    new_response = LLMResponse(query=query, response=response, rating=rating)
    session.add(new_response)
    session.commit()
    session.close()

    logger.info(f"Logged response with Precision: {precision}, Recall: {recall}, F1 Score: {f1_score}")

# Define different RAG approaches
def rag_approach_1(query, relevant_docs):
    # Implementation for RAG Approach 1 with num_typos=2
    return search_typesense(query, relevant_docs, num_typos=2)

def rag_approach_2(query, relevant_docs):
    # Implementation for RAG Approach 2 with num_typos=1
    return search_typesense(query, relevant_docs, num_typos=1)

def evaluate_rag_approaches(query, relevant_docs):
    approaches = [rag_approach_1, rag_approach_2]
    best_approach = None
    best_f1_score = 0

    for approach in approaches:
        try:
            _, _, _, f1_score = approach(query, relevant_docs)
            if f1_score > best_f1_score:
                best_f1_score = f1_score
                best_approach = approach
        except Exception as e:
            logger.error(f"Error evaluating approach {approach.__name__}: {e}")

    if best_approach is None:
        raise ValueError("No valid RAG approach found")

    return best_approach

def main():
    st.title("Search and Q&A Chatbot Github Discussions about Crew AI, Spacy, AllenAI, and more")

    # User input
    user_query = st.text_input("Enter your question:")

    if user_query:
        logger.info(f"User query: {user_query}")

        # Perform RAG evaluation
        relevant_docs = []  # This should be a list of relevant document IDs for the query
        try:
            best_rag_approach = evaluate_rag_approaches(user_query, relevant_docs)
            search_results, precision, recall, f1_score = best_rag_approach(user_query, relevant_docs)
            logger.info(f"Number of search results: {len(search_results['hits'])}")
        except ValueError as e:
            st.error(f"Error: {e}")
            return

        # Extract content for LLM
        combined_context = extract_content_for_llm(search_results, max_tokens=3000)
        logger.info(f"Combined context length: {len(combined_context)} characters")
        logger.info(f"Estimated tokens: {num_tokens_from_string(combined_context)}")
        logger.info(f"Context preview:\n{combined_context[:1000]}...")  # Log the first 1000 characters of the context

        # Set up Langchain components
        llm = OpenAI(temperature=0, max_tokens=256)
        prompt = PromptTemplate(
            input_variables=["question", "context"],
            template="""You are a helpful AI assistant specializing in information about Crew AI. 
            Use ONLY the following context from discussions to answer the user's question. 
            The context contains titles, body text, and comments from relevant discussions about Crew AI. 
            If the context doesn't contain relevant information to answer the question, say that you don't have enough 
            information from the available discussions.

            Context:
            {context}

            User's Question: {question}

            Answer based ONLY on the above context. If the information is not in the context, say you don't have enough information:"""
        )
        chain = prompt | llm

        # Use the chain with the user's query
        logger.info("Sending request to OpenAI")
        response = chain.invoke({"question": user_query, "context": combined_context})
        logger.info(f"OpenAI response: {response}")

        # Display the LLM response to the user
        st.subheader("Answer")
        st.write(response)

        # Add a rating input
        rating = st.slider("Rate the response (1-5)", 1, 5, 3)

        # Add a submit button for the rating
        if st.button("Submit Rating"):
            log_response(user_query, response, float(rating), precision, recall, f1_score)
            st.success("Rating submitted successfully!")

if __name__ == "__main__":
    main()
