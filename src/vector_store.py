
import chromadb

client = chromadb.PersistentClient(path="data/chroma_db")

COLLECTION_NAME = "datheon_documents"

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)


def reset_collection():
    global collection

    client.delete_collection(COLLECTION_NAME)

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    print("Vector database reset successfully.")


def store_documents(documents):
    if not documents:
        print("No documents to store.")
        return

    collection.upsert(
        ids=[doc["chunk_id"] for doc in documents],
        documents=[doc["content"] for doc in documents],
        metadatas=[doc["metadata"] for doc in documents]
    )

    print(f"Successfully stored {len(documents)} chunks")


def search_documents(query_text, allowed_access_tiers, department=None, n_results=3):
    if not allowed_access_tiers:
        raise ValueError("At least one access tier is required")

    conditions = [
        {"access_tier": {"$in": allowed_access_tiers}}
    ]

    if department:
        conditions.append({"department": department})

    filters = conditions[0] if len(conditions) == 1 else {
        "$and": conditions
    }

    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        where=filters
    )

    if not results["documents"][0]:
        print("No authorized matching documents found.")
        return results

    for index, content in enumerate(results["documents"][0]):
        print(f"\nResult {index + 1}")
        print("Content:", content)
        print("Metadata:", results["metadatas"][0][index])
        print("Distance:", results["distances"][0][index])

    return results
