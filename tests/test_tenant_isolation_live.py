
import chromadb

from src import rag_store


def test_cross_tenant_isolation():
    # Create a temporary ChromaDB collection
    client = chromadb.EphemeralClient()

    test_collection = client.create_collection(
        name="tenant_isolation_test",
        metadata={"hnsw:space": "cosine"}
    )

    # Insert documents belonging to two tenants
    test_collection.add(
        ids=["college_a_doc", "college_b_doc"],
        documents=[
            "College A confidential research document.",
            "College B confidential research document."
        ],
        metadatas=[
            {
                "tenant_id": "college_a",
                "access_tier": "confidential",
                "department": "CSE"
            },
            {
                "tenant_id": "college_b",
                "access_tier": "confidential",
                "department": "CSE"
            }
        ]
    )

    # Temporarily replace the collection
    original_collection = rag_store.collection

    try:
        rag_store.collection = test_collection

        # College A must only retrieve its own document
        result_a = rag_store.search_rag_documents(
            query="confidential research document",
            tenant_id="college_a",
            allowed_access_tiers=["confidential"],
            department=None
        )

        assert result_a["ids"][0] == ["college_a_doc"]

        # College B must only retrieve its own document
        result_b = rag_store.search_rag_documents(
            query="confidential research document",
            tenant_id="college_b",
            allowed_access_tiers=["confidential"],
            department=None
        )

        assert result_b["ids"][0] == ["college_b_doc"]

        # Unknown tenant must retrieve nothing
        result_unknown = rag_store.search_rag_documents(
            query="confidential research document",
            tenant_id="college_c",
            allowed_access_tiers=["confidential"],
            department=None
        )

        assert result_unknown["ids"][0] == []

        print("College A isolation: PASSED")
        print("College B isolation: PASSED")
        print("Unknown tenant isolation: PASSED")

    finally:
        rag_store.collection = original_collection


def test_cross_tenant_missing_permissions():
    try:
        rag_store.search_rag_documents(
            query="test",
            tenant_id="college_a",
            allowed_access_tiers=[],
        )
    except ValueError:
        print("Missing permissions protection: PASSED")
    else:
        raise AssertionError("Missing permissions were accepted")
