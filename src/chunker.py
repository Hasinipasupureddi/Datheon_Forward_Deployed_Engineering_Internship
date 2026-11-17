
import re
import math
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction


embedding_function = DefaultEmbeddingFunction()


def cosine_similarity(vector_a, vector_b):
    dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
    norm_a = math.sqrt(sum(a * a for a in vector_a))
    norm_b = math.sqrt(sum(b * b for b in vector_b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def chunk_text(text, chunk_size=800, similarity_threshold=0.35):
    paragraphs = re.split(r"\n\s*\n", text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    if not paragraphs:
        return []

    embeddings = embedding_function(paragraphs)  # Generates paragraph embeddings

    chunks = []
    current_paragraphs = []
    current_embedding = None
    current_length = 0

    for paragraph, embedding in zip(paragraphs, embeddings):
        embedding = list(embedding)

        similarity = (
            cosine_similarity(current_embedding, embedding)
            if current_embedding is not None else 1.0
        )

        if current_paragraphs and (
            similarity < similarity_threshold
            or current_length + len(paragraph) > chunk_size
        ):
            chunks.append("\n\n".join(current_paragraphs))

            current_paragraphs = []
            current_embedding = None
            current_length = 0

        current_paragraphs.append(paragraph)
        current_length += len(paragraph)

        if current_embedding is None:
            current_embedding = embedding
        else:
            current_embedding = [
                (old + new) / 2
                for old, new in zip(current_embedding, embedding)
            ]

    if current_paragraphs:
        chunks.append("\n\n".join(current_paragraphs))

    return chunks


if __name__ == "__main__":
    sample_text = """
A computer network connects multiple devices.

Networks allow information and resource sharing.

Servers manage resources in a computer network.

Routers forward data between different networks.

Switches connect multiple devices within a network.

Firewalls protect networks from unauthorized access.
"""

    result = chunk_text(sample_text)

    for index, chunk in enumerate(result, start=1):
        print(f"\nChunk {index}:")
        print(chunk)
