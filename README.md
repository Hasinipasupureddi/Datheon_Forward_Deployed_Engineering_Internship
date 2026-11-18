# Datheon - Forward Deployed Engineering Internship

An enterprise-oriented document ingestion, multi-tenant Retrieval-Augmented Generation (RAG), and autonomous ERP/CRM field-agent application developed as part of the Datheon Forward Deployed Engineering Internship.

The project demonstrates document processing, vector search, enterprise access control, grounded LLM responses, tool orchestration, human approval workflows, audit logging, and containerized deployment.

## Project Overview

The application is organized around four internship tasks:

1. Legacy Data Ingestion and Vector ETL
2. Enterprise Multi-Tenant RAG with RBAC
3. Autonomous Field Agent with ERP/CRM Tool Orchestration
4. Containerized Deployment and Monitoring

## Implemented Tasks

### Task 1 - Legacy Data Ingestion and Vector ETL

Implemented document ingestion and processing capabilities:

- PDF text extraction.
- OCR fallback for scanned PDF documents.
- Multi-format document reading for PDF, CSV, and Markdown.
- Text cleaning and chunking.
- Metadata enrichment.
- Persistent ChromaDB vector storage.
- Similarity-based document retrieval.

### Task 2 - Enterprise Multi-Tenant RAG with RBAC

Implemented an authenticated enterprise RAG application:

- FastAPI-based REST API.
- JWT authentication with token expiration.
- Argon2 password hashing.
- SQLite-based user authentication.
- Tenant-level document isolation.
- Role-based access control.
- Department and clearance-level filtering.
- ChromaDB vector retrieval.
- Cross-Encoder reranking.
- Rule-based query rewriting.
- Local LLM integration through Ollama and Qwen 2.5 3B.
- Grounded answer generation using retrieved context.
- Source and page-level citation metadata.
- Citation reference validation and abstention handling.

### Task 3 - Autonomous Field Agent with ERP/CRM Tool Orchestration

Implemented an LLM-powered field agent that interacts with a separate mock ERP/CRM REST API.

**Supported tools:**

- `inventory_lookup` - Retrieve inventory information using an SKU.
- `update_lead_status` - Retrieve and update a lead's status.
- `create_support_ticket` - Create a support ticket.

**Agent workflow:**

1. An authenticated user submits an instruction to the field agent.
2. The agent uses Ollama and Qwen 2.5 3B to identify an appropriate tool and its arguments.
3. The application validates the selected tool and arguments against an allowlist and defined schemas.
4. Read-only inventory requests can execute directly.
5. Sensitive write operations are saved as pending approval requests.
6. The authorized request owner reviews and approves or rejects the operation.
7. Approved operations execute through the ERP API client.
8. The application records decisions, actions, observations, approval status, and audit events.

**Additional implementation details:**

- Separate FastAPI-based mock ERP/CRM service.
- SQLite-backed mock ERP data.
- Persistent approval and audit records.
- User and tenant-scoped approval access.
- Approval replay protection.
- Atomic approval state transitions.
- ERP API request timeouts.
- Bounded retries with exponential backoff for eligible transient failures.
- No automatic retry of ticket-creation POST requests, avoiding duplicate side effects.

The mock ERP/CRM service provides a controlled environment for demonstrating enterprise tool orchestration. It is not a connection to a real enterprise ERP system.

### Task 4 - Containerized Deployment and Monitoring

Implemented a local Docker Compose deployment:

- Separate Docker images for the RAG API and mock ERP/CRM service.
- Docker Compose orchestration.
- Environment-based secret configuration.
- Service health checks.
- Container restart policies.
- Internal service communication between containers.
- Host Ollama connectivity through `host.docker.internal`.
- Prometheus metrics endpoint.
- HTTP request count, latency, and error monitoring.
- Localhost-only host port binding.

The current implementation demonstrates local containerized deployment, not deployment inside an actual client VPC.

## Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python 3.12 |
| API framework | FastAPI |
| API server | Uvicorn |
| Vector database | ChromaDB |
| Embeddings | ChromaDB Default Embedding Function |
| Reranking | Sentence Transformers Cross-Encoder |
| LLM | Ollama - Qwen 2.5 3B |
| Authentication | JWT |
| Password hashing | Argon2 |
| Application databases | SQLite |
| PDF processing | PyPDF |
| OCR | Tesseract OCR and Poppler |
| HTTP communication | Requests |
| Monitoring | Prometheus Client |
| Containerization | Docker and Docker Compose |
| Testing | Pytest |

## Project Structure

```text
Project/
├── src/
│   ├── agent_llm.py
│   ├── api.py
│   ├── auth.py
│   ├── chunker.py
│   ├── dependencies.py
│   ├── document_reader.py
│   ├── erp_client.py
│   ├── field_agent.py
│   ├── ingest.py
│   ├── llm.py
│   ├── main.py
│   ├── mock_erp.py
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
│   ├── test_api_security.py
│   ├── test_citation_validation.py
│   ├── test_field_agent.py
│   ├── test_pipeline.py
│   ├── test_query_rewriter.py
│   ├── test_rag_integration.py
│   ├── test_rbac.py
│   └── other test modules
├── data/
│   └── raw/
├── Dockerfile
├── Dockerfile.erp
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

Runtime databases, vector stores, and private documents are maintained locally and are not intended to be committed to the public repository.

## Prerequisites

- Python 3.12
- Docker Desktop with Docker Compose
- Ollama installed and running
- Qwen 2.5 3B model available in Ollama
- Tesseract OCR and Poppler for local OCR workflows

Download the model:

```bash
ollama pull qwen2.5:3b
```

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/Hasinipasupureddi/Datheon_Forward_Deployed_Engineering_Internship.git
cd Datheon_Forward_Deployed_Engineering_Internship
```

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv312
.\.venv312\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local environment file using the example:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and replace the placeholder with a strong, randomly generated `JWT_SECRET_KEY`.

Never commit the actual `.env` file or production secrets.

### 5. Start Ollama

Ensure Ollama is running and the required model is available:

```powershell
ollama list
```

### 6. Start the mock ERP/CRM service

Open a separate terminal, activate the virtual environment, and run:

```powershell
uvicorn src.mock_erp:app --host 127.0.0.1 --port 8001
```

### 7. Start the main API

In another terminal, activate the virtual environment and run:

```powershell
uvicorn src.api:app --host 127.0.0.1 --port 8000
```

The main API is available at:

```text
http://127.0.0.1:8000
```

## Docker Deployment

Make sure Docker Desktop and Ollama are running.

Configure `.env` with a strong JWT secret before starting the application.

Build and start both services:

```powershell
docker compose up -d --build
```

Check service status:

```powershell
docker compose ps
```

View logs:

```powershell
docker compose logs --tail 100 rag-api
docker compose logs --tail 100 erp-mock
```

The Compose configuration publishes:

| Service | Host address |
|---|---|
| RAG API | `127.0.0.1:8000` |
| Mock ERP/CRM | `127.0.0.1:8001` |

The RAG API communicates with the mock ERP/CRM service internally using:

```text
http://erp-mock:8001
```

The container connects to the host Ollama service through:

```text
http://host.docker.internal:11434
```

Stop the services:

```powershell
docker compose down
```

## API Endpoints

### Main RAG and Authentication API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Application information |
| GET | `/health` | Health check |
| POST | `/login` | User authentication |
| GET | `/me` | Authenticated user information |
| POST | `/query` | Authenticated RAG query |
| GET | `/metrics` | Prometheus metrics |

### Autonomous Field Agent API

All field-agent endpoints require authentication.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/agent/run` | Submit an instruction to the agent |
| POST | `/agent/approve/{approval_id}` | Approve or reject a pending operation |
| GET | `/agent/approvals` | View the user's approval requests |
| GET | `/agent/tools` | List available agent tools |
| GET | `/agent/audit` | View tenant-scoped audit records |

### Mock ERP/CRM API

The separate mock ERP/CRM service exposes:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | ERP service health |
| GET | `/inventory/{sku}` | Inventory lookup |
| GET | `/leads/{lead_id}` | Retrieve lead information |
| PATCH | `/leads/{lead_id}/status` | Update lead status |
| POST | `/tickets` | Create a support ticket |
| GET | `/tickets` | List support tickets |

Interactive API documentation:

- Main API: `http://127.0.0.1:8000/docs`
- Mock ERP/CRM: `http://127.0.0.1:8001/docs`

## Example Workflows

### RAG Workflow

1. User authenticates through `/login`.
2. API issues a JWT access token.
3. Authenticated user submits a question to `/query`.
4. The API applies tenant, role, department, and clearance restrictions.
5. Query rewriting improves retrieval.
6. ChromaDB retrieves relevant document chunks.
7. Cross-Encoder reranks retrieved chunks.
8. Ollama generates an answer using authorized context.
9. Citation validation checks referenced source identifiers.
10. API returns the answer and available source metadata.

### Field Agent Workflow

Example instructions:

```text
Check the available quantity for LAPTOP-001.
```

```text
Update lead LEAD-1001 to contacted.
```

```text
Create a high-priority support ticket for the login issue.
```

Read operations can execute directly, while write operations require human approval before execution.

The approval workflow records the request owner, tenant, proposed tool, arguments, status, and relevant audit events.

## Security Features

- JWT-protected application endpoints.
- Argon2 password hashing.
- Tenant-aware document filtering.
- Role and clearance-based access restrictions.
- Department-level filtering for non-admin users.
- Environment-based secret management.
- Tool allowlisting and argument validation.
- Approval ownership and tenant checks.
- Protection against approval replay.
- Persistent audit logging.
- Sensitive databases and private source documents excluded from Git.

## Monitoring

Prometheus metrics are exposed through:

```text
GET /metrics
```

The monitoring middleware tracks:

- HTTP request counts.
- Request latency.
- Request errors.

Health status is available through:

```text
GET /health
```

The application and mock ERP/CRM services also have Docker health checks.

## Testing

Run the complete test suite:

```powershell
python -m pytest -q
```

The complete project test suite was verified with **46 passing tests** in the development environment.

The field-agent integration tests cover:

- Inventory lookup.
- Lead update approval.
- Support ticket approval.
- Rejected operation handling.
- Approval replay protection.
- Approval ownership checks.
- Audit logging.
- Available tool listing.

Validate Docker Compose configuration:

```powershell
docker compose config --quiet
```

Check container health:

```powershell
docker compose ps
```

## Important Data and Deployment Notes

- User databases, vector databases, environment secrets, and private source documents are not intended for public repository commits.
- The `.env.example` file contains only a placeholder secret.
- Ollama must be available for LLM-based answer generation.
- OCR workflows require Tesseract and Poppler.
- The ERP/CRM service is a mock service for controlled testing and demonstration.
- Docker Compose provides local containerized deployment. Actual client VPC deployment requires separate infrastructure configuration, security review, and validation.
- Performance results from local datasets and hardware should not be treated as production benchmarks.
- Tenant isolation and access-control behavior should be validated using independent test data.

## Future Improvements

- Integration with real enterprise ERP/CRM systems.
- Production client VPC deployment.
- Centralized monitoring and dashboards.
- Expanded agent planning and multi-step orchestration.
- Additional load, reliability, and security testing.
- Production-grade secret management and infrastructure automation.

## Project Repository

[Datheon - Forward Deployed Engineering Internship](https://github.com/Hasinipasupureddi/Datheon_Forward_Deployed_Engineering_Internship)

Developed as an internship project demonstrating document processing, enterprise RAG, secure access control, autonomous tool orchestration, human approval workflows, and containerized API deployment.
