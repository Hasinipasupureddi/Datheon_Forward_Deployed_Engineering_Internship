
from vector_store import collection, search_documents


def test_access_filtering():
    internal = collection.get(
        where={"access_tier": "internal"},
        include=["metadatas"]
    )

    confidential = collection.get(
        where={"access_tier": "confidential"},
        include=["metadatas"]
    )

    public = collection.get(
        where={"access_tier": "public"},
        include=["metadatas"]
    )

    print("Internal chunks:", len(internal["ids"]))
    print("Confidential chunks:", len(confidential["ids"]))
    print("Public chunks:", len(public["ids"]))

    assert len(internal["ids"]) > 0
    assert len(confidential["ids"]) > 0
    assert len(public["ids"]) > 0

    assert len(internal["ids"]) + len(confidential["ids"]) + len(public["ids"]) == collection.count()

    results = search_documents(
        "What is a computer network?",
        allowed_access_tiers=["internal"],
        department="CSE"
    )

    assert results["documents"][0]

    for metadata in results["metadatas"][0]:
        assert metadata["access_tier"] == "internal"
        assert metadata["department"] == "CSE"

    print("\nAll access-filtering tests passed!")


if __name__ == "__main__":
    test_access_filtering()
