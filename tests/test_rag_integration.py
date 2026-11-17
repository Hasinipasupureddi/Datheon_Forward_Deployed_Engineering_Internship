import pytest
import chromadb
from src import rag_store


@pytest.fixture
def isolated_rag_collection(monkeypatch):
    client = chromadb.EphemeralClient()

    test_collection = client.create_collection(
        name="datheon_rag_integration_test",
        metadata={"hnsw:space": "cosine"},
        embedding_function=rag_store.collection._embedding_function
    )

    documents = [
        {
            "id": "a_public_cse",
            "content": "Computer networks connect multiple devices.",
            "metadata": {
                "tenant_id": "college_a",
                "access_tier": "public",
                "department": "CSE",
                "source": "network.pdf",
                "page_number": 1
            }
        },
        {
            "id": "a_internal_cse",
            "content": "Internal network architecture details.",
            "metadata": {
                "tenant_id": "college_a",
                "access_tier": "internal",
                "department": "CSE",
                "source": "internal.pdf",
                "page_number": 2
            }
        },
        {
            "id": "a_confidential_cse",
            "content": "Confidential network security policies.",
            "metadata": {
                "tenant_id": "college_a",
                "access_tier": "confidential",
                "department": "CSE",
                "source": "security.pdf",
                "page_number": 3
            }
        },
        {
            "id": "a_public_ece",
            "content": "Public electronics department documents.",
            "metadata": {
                "tenant_id": "college_a",
                "access_tier": "public",
                "department": "ECE",
                "source": "electronics.pdf",
                "page_number": 4
            }
        },
        {
            "id": "b_public_cse",
            "content": "Another tenant's public network documents.",
            "metadata": {
                "tenant_id": "college_b",
                "access_tier": "public",
                "department": "CSE",
                "source": "tenant_b.pdf",
                "page_number": 5
            }
        }
    ]

    test_collection.add(
        ids=[doc["id"] for doc in documents],
        documents=[doc["content"] for doc in documents],
        metadatas=[doc["metadata"] for doc in documents]
    )

    monkeypatch.setattr(
        rag_store,
        "collection",
        test_collection
    )

    yield test_collection

    client.delete_collection("datheon_rag_integration_test")


def test_tenant_isolation(isolated_rag_collection):
    results = rag_store.search_rag_documents(
        query="computer network",
        tenant_id="college_a",
        allowed_access_tiers=["public", "internal", "confidential"],
        n_results=10
    )

    for metadata in results["metadatas"][0]:
        assert metadata["tenant_id"] == "college_a"


def test_public_clearance_filter(isolated_rag_collection):
    results = rag_store.search_rag_documents(
        query="network",
        tenant_id="college_a",
        allowed_access_tiers=["public"],
        n_results=10
    )

    assert results["ids"][0]

    for metadata in results["metadatas"][0]:
        assert metadata["access_tier"] == "public"


def test_internal_clearance_filter(isolated_rag_collection):
    results = rag_store.search_rag_documents(
        query="network",
        tenant_id="college_a",
        allowed_access_tiers=["public", "internal"],
        n_results=10
    )

    tiers = {
        metadata["access_tier"]
        for metadata in results["metadatas"][0]
    }

    assert tiers.issubset({"public", "internal"})
    assert "confidential" not in tiers


def test_confidential_clearance_filter(isolated_rag_collection):
    results = rag_store.search_rag_documents(
        query="network",
        tenant_id="college_a",
        allowed_access_tiers=["public", "internal", "confidential"],
        n_results=10
    )

    tiers = {
        metadata["access_tier"]
        for metadata in results["metadatas"][0]
    }

    assert "confidential" in tiers


def test_department_filter(isolated_rag_collection):
    results = rag_store.search_rag_documents(
        query="documents",
        tenant_id="college_a",
        allowed_access_tiers=["public", "internal", "confidential"],
        department="CSE",
        n_results=10
    )

    assert results["ids"][0]

    for metadata in results["metadatas"][0]:
        assert metadata["department"] == "CSE"


def test_unknown_tenant_gets_no_results(isolated_rag_collection):
    results = rag_store.search_rag_documents(
        query="network",
        tenant_id="college_unknown",
        allowed_access_tiers=["public", "internal"],
        n_results=10
    )

    assert results["ids"][0] == []
    assert results["documents"][0] == []


def test_missing_tenant_is_rejected(isolated_rag_collection):
    with pytest.raises(ValueError):
        rag_store.search_rag_documents(
            query="network",
            tenant_id=None,
            allowed_access_tiers=["public"]
        )


def test_missing_access_permissions_are_rejected(isolated_rag_collection):
    with pytest.raises(ValueError):
        rag_store.search_rag_documents(
            query="network",
            tenant_id="college_a",
            allowed_access_tiers=[]
        )
