
"""Command-line entry point for the legacy ingestion and retrieval demo."""

import time
import vector_store
from ingest import ingest_directory


def main():
    """Reset the sample collection, ingest documents, and print timings."""
    print("Welcome to Enterprise AI Document Assistant!")

    metadata = {
        "sample.pdf": {
            "department": "CSE",
            "access_tier": "internal"
        },
        "sample1.pdf": {
            "department": "CSE",
            "access_tier": "confidential"
        },
        "sample.csv": {
            "department": "AI_ML",
            "access_tier": "public"
        },
        "sample.md": {
            "department": "AI_ML",
            "access_tier": "public"
        }
    }

    # Reset the sample database before a fresh run
    vector_store.reset_collection()

    start = time.perf_counter()
    documents = ingest_directory("data/raw", metadata)
    ingestion_time = time.perf_counter() - start

    start = time.perf_counter()
    vector_store.store_documents(documents)
    storage_time = time.perf_counter() - start

    start = time.perf_counter()
    vector_store.search_documents(
        "What is a computer network?",
        allowed_access_tiers=["internal"],
        department="CSE"
    )
    search_time = time.perf_counter() - start

    print("\n--- Pipeline Benchmark ---")
    print("Total chunks:", len(documents))
    print("Database records:", vector_store.collection.count())
    print(f"Document ingestion time: {ingestion_time:.4f} seconds")
    print(f"Embedding and storage time: {storage_time:.4f} seconds")
    print(f"Search time: {search_time:.4f} seconds")


if __name__ == "__main__":
    main()
