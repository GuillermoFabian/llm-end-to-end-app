# RAG Q&A System with GitHub Discussions

## Project Overview

This project implements a Retrieval-Augmented Generation (RAG) Q&A system using GitHub Discussions as the knowledge base. It leverages several technologies to create an efficient and monitored system for answering questions based on GitHub content.

## Table of Contents

1. [Project Scope](#project-scope)
2. [Technologies Used](#technologies-used)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [Running the RAG Q&A System](#running-the-rag-qa-system)
7. [Monitoring](#monitoring)

## Project Scope

This project aims to create a RAG Q&A system that:

1. Ingests GitHub Discussions data into a Typesense database using Mage AI for data orchestration.
2. Implements a RAG flow to query the knowledge base and generate answers using an LLM.
3. Monitors the system's performance and user interactions using Grafana.
4. Stores metadata and logs in a PostgreSQL database.

## Technologies Used


- **Mage AI**: An open-source data pipeline tool used for ingesting GitHub Discussions data into Typesense.
- **Typesense**: A fast, typo-tolerant search engine used as our vector database for storing and querying embeddings.
- **Grafana**: An open-source analytics and monitoring platform used to visualize system performance and user interactions.
- **PostgreSQL**: A powerful, open-source relational database used for storing metadata and logs.
- **Docker**: Used for containerizing and managing our application components.

## Installation

### Prerequisites

- Docker and Docker Compose
- Git

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/rag-qa-system.git
   cd rag-qa-system
   ```

2. Create a `.env` file in each service folder (see [Configuration](#configuration) section).

3. Build and start the containers for each service:
   ```
   cd mage-ai && docker-compose up -d
   cd ../typesense && docker-compose up -d
   cd ../grafana && docker-compose up -d
   cd ../postgres && docker-compose up -d
   ```

This will start the following services:
- Mage AI: http://localhost:6789
- Typesense: http://localhost:8108
- Grafana: http://localhost:3000
- PostgreSQL: localhost:5432 (backend no interface)

## Configuration

Create a `.env` file in the project root with the following content:


OPENAI_API_KEY=your_openai_api_key
TYPESENSE_API_KEY=your_typesense_api_key
POSTGRES_DB=rag_qa_db
POSTGRES_USER=rag_qa_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
GITHUB_TOKEN=your_github_personal_access_token



Replace the placeholder values with your actual API keys and credentials.

## Usage

1. Access the Mage AI interface at http://localhost:6789 to set up and run the data ingestion pipeline.

   ![Mage AI Dashboard](/img/mage_ai_dashboard.png)

2. Once the data is ingested, you can use the provided Python scripts to query the RAG system.

3. Monitor the system's performance and user interactions through Grafana at http://localhost:3000.

   ![Grafana Dashboard](/img/grafana_logs.png)

## Running the RAG Q&A System

The main component of this project is the `rag_flow.py` script, which starts a Streamlit app allowing users to interact with the RAG Q&A system.

To run the Streamlit app:

1. Ensure all services are running (Mage AI, Typesense, PostgreSQL, and Grafana).

2. Navigate to the project directory:
   ```
   cd rag-qa-system
   ```

3. Install the required Python packages if you haven't already:
   ```
   pip install -r requirements.txt
   ```

4. Run the Streamlit app:
   ```
   streamlit run rag_flow.py
   ```

5. Open your web browser and go to `http://localhost:8501` to access the RAG Q&A interface.

![Streamlit RAG Q&A Interface](/img/streamlit_rag_qa.png)

### Using the RAG Q&A Interface

1. Enter your question in the text input field.
2. Click the "Ask" button or press Enter to submit your question.
3. The system will process your question, retrieve relevant information from the GitHub Discussions, and generate an answer.
4. The answer will be displayed along with relevant source information.

![Streamlit Answer Display](/img/streamlit_answer.png)

You can ask multiple questions and the chat history will be displayed in the interface.

### Performance and Monitoring

As you use the RAG Q&A system, performance metrics and user interactions are logged and can be monitored through the Grafana dashboard.

## Monitoring

Access Grafana at http://localhost:3000 to view dashboards for:
- User interaction statistics

Custom dashboards can be created to track specific metrics.

For more detailed information on each component, refer to their respective documentation:
- [Mage AI Documentation](https://docs.mage.ai/)
- [Typesense Documentation](https://typesense.org/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)