# Datheon - Forward Deployed Engineering Internship

An enterprise-oriented document ingestion and multi-tenant Retrieval-Augmented Generation (RAG) application developed as part of the Datheon Forward Deployed Engineering Internship.

## Project Overview

This project demonstrates document ingestion, text extraction, chunking, vector storage, tenant-aware retrieval, role-based access control, reranking, LLM-based answer generation, citation validation, and containerized API deployment.

## Implemented Tasks

### Task 1 - Legacy Data Ingestion and Vector ETL

- PDF text extraction.
- OCR fallback for scanned documents.
- Multi-format document reading (PDF, CSV, Markdown).
- Semantic text chunking.
- Metadata enrichment.
- Persistent ChromaDB vector storage.
- Similarity-based document retrieval.

### Task 2 - Enterprise Multi-Tenant RAG with RBAC

- FastAPI-based REST API.
- JWT authentication.
- Argon2 password hashing.
- SQLite user authentication database.
- Tenant-level data isolation.
- Role-based access control.
- Department and clearance-level filtering.
- ChromaDB vector retrieval.
- Cross-Encoder reranking.
- Query rewriting.
- Local LLM integration through Ollama.
- Source and page-level citations.
- Citation reference validation and abstention handling.

### Task 4 - Containerized Deployment and Monitoring

- Dockerfile-based application packaging.
- Docker Compose deployment.
- Environment-based secret configuration.
- Health-check endpoint.
- Prometheus metrics endpoint.
- Request count, latency, and error monitoring.
- Container restart policy.
- Localhost-only host port binding.

## Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python 3.12 |
| API framework | FastAPI |
| API server | Uvicorn |
| Vector database | ChromaDB |
| Embeddings | ChromaDB embedding function |
| Reranking | Sentence Transformers Cross-Encoder |
| LLM | Ollama - Qwen 2.5 3B |
| Authentication | JWT |
| Password hashing | Argon2 |
| User database | SQLite |
| Document extraction | PyPDF, Tesseract OCR, Poppler |
| Monitoring | Prometheus Client |
| Containerization | Docker and Docker Compose |
| Testing | Pytest |

## Project Structure

```text
Project/
├── src/
│   ├── api.py
│   ├── auth.py
│   ├── chunker.py
│   ├── document_reader.py
│   ├── ingest.py
│   ├── llm.py
│   ├── main.py
│   ├── monitoring.py
│   ├── multi_format_reader.py
│   ├── page_chunker.py
│   ├── page_reader.py
│   ├── query_rewriter.py
│   ├── rag_ingest.py
│   ├── rag_store.py
│   ├── reranker.py
│   └── vector_store.py
├── tests/
├── data/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .gitignore
└── README.md
```

## Prerequisites

- Python 3.12
- Docker Desktop with Docker Compose
- Ollama installed and running
- Qwen 2.5 3B model available in Ollama
- Tesseract OCR and Poppler for local OCR workflows

Pull the model if it is not already installed:

```bash
ollama pull qwen2.5:3b
```

## Local Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv312
.\.venv312\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Configure the environment file:

Create a `.env` file containing a strong, randomly generated `JWT_SECRET_KEY`.

Do not commit `.env` or actual credentials to GitHub.

Start the API:

```powershell
uvicorn src.api:app --host 127.0.0.1 --port 8000
```

## Docker Deployment

Make sure Docker Desktop and Ollama are running.

Configure `.env` with the required JWT secret before starting the application.

Build and start the service:

```powershell
docker compose up -d --build
```

Check container status:

```powershell
docker compose ps
```

View logs:

```powershell
docker compose logs --tail 100 rag-api
```

The Compose configuration publishes the API on localhost:

```text
127.0.0.1:8000
```

The container connects to the host Ollama service through `host.docker.internal`.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Application information |
| GET | `/health` | Health check |
| POST | `/login` | User authentication |
| GET | `/me` | Authenticated user information |
| POST | `/query` | Authenticated RAG query |
| GET | `/metrics` | Prometheus metrics |

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

## Example RAG Workflow

1. User authenticates through `/login`.
2. API issues a JWT access token.
3. Authenticated user submits a question to `/query`.
4. The API applies tenant, role, department, and clearance restrictions.
5. Query rewriting improves retrieval.
6. ChromaDB retrieves relevant document chunks.
7. Cross-Encoder reranks retrieved chunks.
8. Ollama generates an answer using authorized context.
9. Citation validation checks referenced source identifiers.
10. API returns the answer, citations, and source metadata.

## Security Features

- JWT-protected endpoints.
- Argon2 password hashing.
- Tenant-aware document filtering.
- Role and clearance-based access restrictions.
- Department-level filtering for non-admin users.
- Environment-based secret management.
- Sensitive databases and source documents excluded from Git.

## Monitoring

Prometheus metrics are exposed through:

```text
GET /metrics
```

The monitoring middleware tracks HTTP request counts, request latency, and request errors.

Health status is available through:

```text
GET /health
```

## Testing

Run the complete test suite:

```powershell
python -m pytest tests -q
```

Validate Docker Compose configuration:

```powershell
docker compose config --quiet
```

## Important Data and Deployment Notes

- User databases, vector databases, environment secrets, and private source documents are not intended for public repository commits.
- Ollama must be available to the container for LLM-based answer generation.
- OCR requires Tesseract and Poppler.
- Docker Compose provides a local containerized deployment. A production client VPC deployment requires separate infrastructure configuration and validation.
- Tenant isolation and access-control behavior should be validated using independent test data.

## Project Repository

Datheon Forward Deployed Engineering Internship

Developed as an internship project demonstrating document processing, enterprise RAG, access control, and containerized API deployment.
