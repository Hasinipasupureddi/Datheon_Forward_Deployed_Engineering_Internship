
"""FastAPI application for authenticated, tenant-aware document retrieval."""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import jwt

try:
    from .dependencies import get_current_user
except ImportError:
    from dependencies import get_current_user

try:
    from .auth import (
        get_user_by_username,
        get_user_by_id,
        verify_password,
        create_access_token,
        decode_access_token
    )
    from .rag_store import search_rag_documents
    from .reranker import rerank_results
    from .query_rewriter import rewrite_query
    from .llm import generate_grounded_answer

except ImportError:
    from auth import (
        get_user_by_username,
        get_user_by_id,
        verify_password,
        create_access_token,
        decode_access_token
    )
    from rag_store import search_rag_documents
    from reranker import rerank_results
    from query_rewriter import rewrite_query
    from llm import generate_grounded_answer


app = FastAPI(
    title="Datheon Enterprise RAG API",
    description=(
        "Multi-tenant RAG with JWT authentication, "
        "clearance-based RBAC, query rewriting, "
        "Cross-Encoder reranking and grounded LLM answers"
    ),
    version="2.3.0"
)

CLEARANCE_ACCESS = {
    "public": ["public"],
    "internal": ["public", "internal"],
    "confidential": ["public", "internal", "confidential"]
}


class LoginRequest(BaseModel):
    username: str
    password: str


class QueryRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1000)



@app.get("/")
def home():
    """Return basic service information for operators and health probes."""
    return {
        "message": "Datheon Enterprise RAG API is running",
        "version": "2.3.0"
    }


@app.get("/health")
def health():
    """Return the liveness response used by local and Docker checks."""
    return {"status": "healthy"}


@app.post("/login")
def login(request: LoginRequest):
    """Authenticate a user without revealing which credential failed."""
    user = get_user_by_username(request.username)

    if (
        not user
        or not user["is_active"]
        or not verify_password(
            request.password,
            user["password_hash"]
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    token = create_access_token(user["user_id"])

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@app.get("/me")
def get_profile(user: dict = Depends(get_current_user)):
    """Return non-secret identity and authorization attributes."""
    return {
        "username": user["username"],
        "role": user["role"],
        "tenant_id": user["tenant_id"],
        "department": user["department"],
        "clearance_level": user["clearance_level"]
    }


@app.post("/query")
def query_documents(
    request: QueryRequest,
    user: dict = Depends(get_current_user)
):
    """Retrieve, rerank, and ground an answer within the user's authorization scope."""
    # Step 1: Validate clearance
    clearance = user["clearance_level"]

    if clearance not in CLEARANCE_ACCESS:
        raise HTTPException(
            status_code=403,
            detail="Invalid user clearance level"
        )

    # Step 2: Validate role
    if user["role"] not in ["admin", "manager", "employee"]:
        raise HTTPException(
            status_code=403,
            detail="Invalid user role"
        )

    if user["role"] != "admin" and not user["department"]:
        raise HTTPException(
            status_code=403,
            detail="Department assignment is required"
        )

    allowed_tiers = CLEARANCE_ACCESS[clearance]

    department = (
        None if user["role"] == "admin"
        else user["department"]
    )

    # Step 3: Rewrite original query
    rewritten_query = rewrite_query(request.query)

    # Apply tenant, clearance, and department filters before retrieval so
    # unauthorized chunks cannot reach reranking or the language model.
    # Step 4: Retrieve only authorized documents
    results = search_rag_documents(
        query=rewritten_query,
        tenant_id=user["tenant_id"],
        allowed_access_tiers=allowed_tiers,
        department=department,
        n_results=15
    )

    # Step 5: Rerank retrieved documents
    ranked_results = rerank_results(
        query=request.query,
        results=results,
        top_k=5
    )

    # Step 6: Prepare detailed retrieval information
    sources = []

    for item in ranked_results:
        metadata = item["metadata"]

        sources.append({
            "content": item["content"],
            "source": metadata["source"],
            "page_number": metadata["page_number"] or None,
            "department": metadata["department"],
            "access_tier": metadata["access_tier"],
            "vector_distance": item["distance"],
            "rerank_score": item["rerank_score"]
        })

    # Step 7: Generate grounded answer using Ollama
    try:
        generated = generate_grounded_answer(
            query=request.query,
            retrieved_chunks=ranked_results
        )

    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="The local LLM service is unavailable. Please try again."
        )

    # Step 8: Return final RAG response

    return {
        "original_query": request.query,
        "rewritten_query": rewritten_query,
        "tenant_id": user["tenant_id"],
        "role": user["role"],
        "clearance_level": clearance,
        "allowed_access_tiers": allowed_tiers,
        "retrieval_method": "ChromaDB + Cross-Encoder",
        "generation_model": "Ollama - qwen2.5:3b",
        "answer": generated["answer"],
        "citations": generated["citations"],
        "abstained": generated["abstained"],
        "citation_validation": generated["citation_validation"],
        "sources": sources,
        "results": sources,
        "result_count": len(sources)
    }



from src.monitoring import install_metrics
install_metrics(app)

# Task 3: Autonomous Field Agent routes
try:
    from .field_agent import router as field_agent_router
except ImportError:
    from field_agent import router as field_agent_router

app.include_router(field_agent_router, dependencies=[Depends(get_current_user)])

