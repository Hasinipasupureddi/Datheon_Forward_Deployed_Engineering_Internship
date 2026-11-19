
"""Prepare tenant-scoped, page-aware documents for the RAG collection."""

from pathlib import Path
from datetime import date

try:
    from .page_reader import read_pdf_pages
    from .page_chunker import chunk_pages
    from .chunker import chunk_text
except ImportError:
    from page_reader import read_pdf_pages
    from page_chunker import chunk_pages
    from chunker import chunk_text


def ingest_for_rag(
    file_path,
    tenant_id="demo",
    department="General",
    access_tier="public"
):
    """Ingest a supported file and attach tenant, access, and page metadata."""
    file_path = Path(file_path)
    extension = file_path.suffix.lower()

    # PDF: Extract text page by page
    if extension == ".pdf":
        pages = read_pdf_pages(file_path)
        chunks = chunk_pages(pages)

    # CSV: Read and convert records into text
    elif extension == ".csv":
        import csv

        records = []

        with open(file_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                records.append(row)

        text = "\n".join(
            " | ".join(
                f"{key}: {value}" for key, value in record.items()
            )
            for record in records
        )

        text_chunks = chunk_text(text)

        chunks = [
            {
                "content": chunk,
                "page_number": None,
                "chunk_index": index
            }
            for index, chunk in enumerate(text_chunks)
        ]

    # Markdown: Read text
    elif extension == ".md":
        with open(file_path, "r", encoding="utf-8") as file:
            text = file.read()

        text_chunks = chunk_text(text)

        chunks = [
            {
                "content": chunk,
                "page_number": None,
                "chunk_index": index
            }
            for index, chunk in enumerate(text_chunks)
        ]

    else:
        raise ValueError("Unsupported file format")

    documents = []

    for index, chunk in enumerate(chunks):
        documents.append({
            "chunk_id": (
                f"{tenant_id}_{file_path.stem}_"
                f"{extension[1:]}_{index}"
            ),
            "content": chunk["content"],
            "metadata": {
                "tenant_id": tenant_id,
                "source": file_path.name,
                "department": department,
                "access_tier": access_tier,
                "file_type": extension,
                "page_number": chunk["page_number"] or 0,
                "chunk_index": chunk["chunk_index"],
                "ingestion_date": date.today().isoformat()
            }
        })

    return documents
