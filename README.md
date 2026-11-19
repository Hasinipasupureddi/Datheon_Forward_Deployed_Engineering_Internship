# Datheon – Forward Deployed Engineering Internship

An enterprise-oriented document ingestion, multi-tenant Retrieval-Augmented Generation (RAG), and autonomous ERP/CRM field-agent application developed as part of the Datheon Forward Deployed Engineering Internship.

The project demonstrates document processing, vector search, enterprise access control, grounded LLM responses, tool orchestration, human approval workflows, audit logging, containerized deployment, and monitoring.

## Project Overview

The application is organized around four internship tasks:

1. Legacy Data Ingestion and Vector ETL
2. Enterprise Multi-Tenant RAG with RBAC
3. Autonomous Field Agent with ERP/CRM Tool Orchestration
4. Containerized Deployment and Monitoring

## Implemented Tasks

### Task 1 – Legacy Data Ingestion and Vector ETL

Implemented document ingestion and processing capabilities:

- PDF text extraction.
- OCR fallback for scanned PDF documents.
- Multi-format document reading for PDF, CSV, and Markdown.
- Text cleaning and chunking.
- Metadata enrichment.
- Persistent ChromaDB vector storage.
- Similarity-based document retrieval.

**Implementation:** Document readers, chunking modules, ingestion pipeline, vector storage, and pipeline tests.

### Task 2 – Enterprise Multi-Tenant RAG with RBAC

Implemented an authenticated enterprise RAG application:

- FastAPI-based REST API.
- JWT authentication with token expiration.
- Argon2 password hashing.
- SQLite-based user authentication.
- Tenant-level document isolation.
- Role-based access control.
- Department and clearance-level filtering.
- ChromaDB vector retrieval.
- Cross-Encoder reranking using Sentence Transformers.
- Rule-based query rewriting.
- Local LLM integration through Ollama and Qwen 2.5 3B.
- Grounded answer generation using retrieved context.
- Source and page-level citation metadata.
- Citation reference validation.
- Abstention handling when relevant supporting information is unavailable.

**Implementation:** Authentication, retrieval, reranking, query rewriting, LLM generation, citation validation, and protected FastAPI endpoints.

### Task 3 – Autonomous Field Agent with ERP/CRM Tool Orchestration

Implemented an LLM-powered field agent that interacts with a separate mock ERP/CRM REST API.

#### Supported Tools

- `inventory_lookup` – Retrieve inventory information using an SKU.
- `update_lead_status` – Update a lead's status.
- `create_support_ticket` – Create a support ticket.

#### Agent Workflow

1. An authenticated user submits an instruction to the field agent.
2. The agent uses Ollama and Qwen 2.5 3B to identify an appropriate tool and its arguments.
3. The application validates the selected tool and arguments against an allowlist and defined schemas.
4. Read-only inventory requests can execute directly.
5. Sensitive write operations are saved as pending approval requests.
6. The authorized request owner reviews and approves or rejects the operation.
7. Approved operations execute through the ERP API client.
8. The application records decisions, actions, observations, approval status, and audit events.

#### Additional Implementation Details

- Separate FastAPI-based mock ERP/CRM service.
- SQLite-backed mock ERP data.
- Persistent approval and audit records.
- User- and tenant-scoped approval access.
- Approval replay protection.
- Atomic approval state transitions.
- ERP API request timeouts.
- Bounded retries with exponential backoff for eligible transient failures.
- No automatic retry of ticket-creation POST requests, avoiding duplicate side effects.

The mock ERP/CRM service provides a controlled environment for demonstrating enterprise tool orchestration. It is not connected to a real enterprise ERP system.

### Task 4 – Containerized Deployment and Monitoring

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
- Local LLM prompt and completion token usage metrics.
- Localhost-only host port binding.

The application was built and run using Docker Compose. Both containers were verified as healthy, and the API, monitoring endpoint, and RAG query workflow were tested.

**Deployment scope:** The current implementation demonstrates local containerized deployment, not deployment inside an actual client VPC. Client-specific VPC deployment requires separate infrastructure, networking, secrets, and security configuration.

## Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python 3.12 |
| API framework | FastAPI |
| API server | Uvicorn |
| Vector database | ChromaDB |
| Embeddings | ChromaDB Default Embedding Function |
| Reranking | Sentence Transformers Cross-Encoder |
| LLM | Ollama – Qwen 2.5 3B |
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
│   └── test_rbac.py
├── scripts/
│   ├── benchmark.py
│   └── benchmark_report.md
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

Runtime databases, vector stores, private documents, and environment secrets are maintained locally and are not intended to be committed to the public repository.

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

### 1. Clone the Repository

```bash
git clone https://github.com/Hasinipasupureddi/Datheon_Forward_Deployed_Engineering_Internship.git
cd Datheon_Forward_Deployed_Engineering_Internship
```

### 2. Create and Activate a Virtual Environment

```powershell
python -m venv .venv312
.\.venv312\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a local environment file using the example:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and replace the placeholder with a strong, randomly generated `JWT_SECRET_KEY`.

Never commit the actual `.env` file, passwords, access tokens, or production secrets.

### 5. Start Ollama

Ensure Ollama is running and the required model is available:

```powershell
ollama list
```

### 6. Start the Mock ERP/CRM Service

Open a separate terminal, activate the virtual environment, and run:

```powershell
uvicorn src.mock_erp:app --host 127.0.0.1 --port 8001
```

### 7. Start the Main API

In another terminal, activate the virtual environment and run:

```powershell
uvicorn src.api:app --host 127.0.0.1 --port 8000
```

The main API is available at:

`http://127.0.0.1:8000`

## Docker Deployment

Ensure Docker Desktop and Ollama are running.

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

`http://erp-mock:8001`

The container connects to the host Ollama service through:

`http://host.docker.internal:11434`

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

The monitoring implementation tracks:

- HTTP request counts.
- Request latency.
- HTTP errors.
- LLM prompt token usage.
- LLM completion token usage.

The LLM token counter is exposed as:

`datheon_llm_tokens_total`

Token metrics include model and token type labels.

Health status is available through:

```text
GET /health
```

The application and mock ERP/CRM services also have Docker health checks.

## Client Integration Guide

### 1. Start the Services

Ensure Docker Desktop and Ollama are running. Configure the required environment variables using `.env.example` and your local `.env` file.

Start the services:

```powershell
docker compose up -d --build
docker compose ps
```

### 2. Verify Service Availability

- API documentation: `http://localhost:8000/docs`
- Health endpoint: `http://localhost:8000/health`
- Prometheus metrics: `http://localhost:8000/metrics`
- Mock ERP health: `http://localhost:8001/health`

### 3. Authenticate

Send a POST request to `/login` with JSON credentials:

```json
{
  "username": "your_username",
  "password": "your_password"
}
```

Use the returned access token as a Bearer token in subsequent authenticated API requests.

### 4. Submit a RAG Query

Send a POST request to `/query` with a valid Bearer token and a JSON request body matching the API schema.

The response includes the generated answer, source citations, and citation validation status.

### 5. Monitor the Service

Configure Prometheus-compatible monitoring to scrape `/metrics`.

Available metrics include HTTP request counts, request latency, HTTP errors, and local LLM token usage.

### 6. Security and Handoff Checklist

- Generate a unique, strong JWT secret for each deployment.
- Never commit `.env`, passwords, access tokens, or private documents.
- Configure HTTPS and network access controls before external exposure.
- Restrict service access to authorized client networks.
- Back up persistent application data securely.
- Validate tenant isolation and authorization with client-specific test accounts.
- Review logs, health checks, and monitoring before handoff.

### Deployment Scope

This guide covers local Docker Compose integration. Client VPC deployment requires client-specific networking, infrastructure, secrets, and security configuration before production use.

## Testing

Run the complete test suite:

```powershell
$env:JWT_SECRET_KEY = "test-only-placeholder"
python -m pytest -q
```

The test suite requires `JWT_SECRET_KEY`; the command above uses a process-local
placeholder and does not create or expose a production secret.

The project test suite was verified with **46 passing tests** in the development environment.

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

## Task 4 – Latency Benchmark Results

Local Docker deployment benchmarked on **19 November 2026**.

| Endpoint | Requests | Average | Minimum | Maximum |
|---|---:|---:|---:|---:|
| Health | 10 | 2.69 ms | 2.13 ms | 4.76 ms |
| RAG Query | 3 | 13,540.13 ms | 5,424.27 ms | 29,671.86 ms |

- Successful grounded RAG queries: 3/3
- LLM: Ollama Qwen 2.5 3B
- Environment: Local Docker deployment

The benchmark script is available at `scripts/benchmark.py`.

Detailed results are available in `scripts/benchmark_report.md`.

These are local benchmark observations, not production SLA guarantees. Results depend on the local machine, model, data, and runtime conditions.

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

[Datheon – Forward Deployed Engineering Internship](https://github.com/Hasinipasupureddi/Datheon_Forward_Deployed_Engineering_Internship)

Developed as an internship project demonstrating document processing, enterprise RAG, secure access control, autonomous tool orchestration, human approval workflows, and containerized API deployment.
