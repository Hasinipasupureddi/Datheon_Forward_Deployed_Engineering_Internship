
"""Store and retrieve tenant-isolated RAG document chunks."""

import chromadb

client = chromadb.PersistentClient(
    path="data/rag_chroma_db"
)

COLLECTION_NAME = "datheon_rag_v2"

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)


def store_rag_documents(documents):
    """Upsert RAG chunks using their stable tenant-scoped IDs."""
    if not documents:
        return 0

    collection.upsert(
        ids=[doc["chunk_id"] for doc in documents],
        documents=[doc["content"] for doc in documents],
        metadatas=[doc["metadata"] for doc in documents]
    )

    return len(documents)


def search_rag_documents(
    query,
    tenant_id,
    allowed_access_tiers,
    department=None,
    n_results=5
):
    """Query only documents allowed by tenant, clearance, and department."""
    if not tenant_id:
        raise ValueError("Tenant ID is required")

    if not allowed_access_tiers:
        raise ValueError("Access permissions are required")

    if collection.count() == 0:
        return {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        }

    conditions = [
        {"tenant_id": tenant_id},
        {"access_tier": {"$in": allowed_access_tiers}}
    ]

    if department:
        conditions.append(
            {"department": department}
        )

    where_filter = {"$and": conditions}

    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, collection.count()),
        where=where_filter
    )

    return results
