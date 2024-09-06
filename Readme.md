# RAG Q&A System with GitHub Discussions

![Project Overview](/img/project_overview.png)

This project implements a Retrieval-Augmented Generation (RAG) Q&A system using GitHub Discussions as the knowledge base. It leverages several technologies to create an efficient and monitored system for answering questions based on GitHub content.

## Table of Contents

1. [Project Scope](#project-scope)
2. [Technologies Used](#technologies-used)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [Monitoring](#monitoring)

## Project Scope

This project aims to create a RAG Q&A system that:

1. Ingests GitHub Discussions data into a Typesense database using Mage AI for data orchestration.
2. Implements a RAG flow to query the knowledge base and generate answers using an LLM.
3. Monitors the system's performance and user interactions using Grafana.
4. Stores metadata and logs in a PostgreSQL database.

## Technologies Used

![Tech Stack](/img/tech_stack.png)

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

2. Create a `.env` file in the project root (see [Configuration](#configuration) section).

3. Build and start the containers:
   ```
   docker-compose up -d
   ```

This command will start the following services:
- Mage AI: http://localhost:6789
- Typesense: http://localhost:8108
- Grafana: http://localhost:3000
- PostgreSQL: localhost:5432

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

   ![Grafana Dashboard](/img/grafana_dashboard.png)

## Monitoring

Access Grafana at http://localhost:3000 to view dashboards for:
- Query performance
- User interaction statistics
- System resource usage

Custom dashboards can be created to track specific metrics relevant to your use case.

For more detailed information on each component, refer to their respective documentation:
- [Mage AI Documentation](https://docs.mage.ai/)
- [Typesense Documentation](https://typesense.org/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)