
"""Chunk page-aware PDF text while preserving source page metadata."""

try:
    from .chunker import chunk_text
except ImportError:
    from chunker import chunk_text


def chunk_pages(pages, chunk_size=800, similarity_threshold=0.35):
    """Return chunks with page numbers suitable for citation generation."""
    all_chunks = []

    for page in pages:
        page_number = page["page_number"]
        content = page["content"]

        if not content.strip():
            continue

        page_chunks = chunk_text(
            content,
            chunk_size=chunk_size,
            similarity_threshold=similarity_threshold
        )

        for chunk_index, chunk in enumerate(page_chunks):
            all_chunks.append({
                "content": chunk,
                "page_number": page_number,
                "chunk_index": chunk_index
            })

    return all_chunks
