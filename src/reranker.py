
"""Rerank vector results with a local Sentence Transformers Cross-Encoder."""

from sentence_transformers import CrossEncoder


MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_model = None


def get_reranker():
    """Load the CPU reranker lazily so import does not load the model."""
    global _model

    if _model is None:
        print("Loading Cross-Encoder model...")

        _model = CrossEncoder(
            MODEL_NAME,
            device="cpu",
            max_length=512
        )

        print("Cross-Encoder loaded successfully!")

    return _model


def rerank_results(query, results, top_k=5):
    """Score retrieved query-document pairs and return the highest-ranked rows."""
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not documents:
        return []

    model = get_reranker()

    pairs = [
        (query, document)
        for document in documents
    ]

    scores = model.predict(
        pairs,
        batch_size=8,
        show_progress_bar=False
    )

    ranked = []

    for content, metadata, distance, score in zip(
        documents,
        metadatas,
        distances,
        scores
    ):
        ranked.append({
            "content": content,
            "metadata": metadata,
            "distance": float(distance),
            "rerank_score": float(score)
        })

    ranked.sort(
        key=lambda item: item["rerank_score"],
        reverse=True
    )

    return ranked[:top_k]
