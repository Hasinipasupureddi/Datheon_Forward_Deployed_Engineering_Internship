
from multi_format_reader import load_document
from chunker import chunk_text
from pathlib import Path
from datetime import date


def ingest_document(file_path, department="General", access_tier="public"):
    file_path = Path(file_path)  # Converts the path into a Path object
    text = load_document(file_path)  # Extracts document content
    chunks = chunk_text(text)  # Divides content into chunks

    documents = []  # Stores processed document chunks
    for index, chunk in enumerate(chunks):
        documents.append({
            "chunk_id": f"{file_path.stem}_{file_path.suffix.lower().replace('.', '')}_{index}",
            "source": file_path.name,
            "content": chunk,
            "metadata": {
                "department": department,
                "access_tier": access_tier,
                "ingestion_date": date.today().isoformat(),
                "file_type": file_path.suffix.lower(),
                "chunk_index": index
            }
        })  # Stores each chunk with its metadata

    return documents


def ingest_directory(directory, metadata_by_file=None):
    directory = Path(directory)
    all_documents = []  # Stores chunks from all supported files

    for file_path in directory.iterdir():
        if file_path.suffix.lower() not in [".pdf", ".csv", ".md"]:
            continue

        settings = (metadata_by_file or {}).get(file_path.name, {})

        documents = ingest_document(file_path, **settings)
        all_documents.extend(documents)  # Adds chunks to the batch

        print(f"Processed {file_path.name}: {len(documents)} chunks")

    return all_documents


if __name__ == "__main__":
    result = ingest_document(
        "data/raw/sample.pdf",
        department="CSE",
        access_tier="internal"
    )

    print(f"Total chunks: {len(result)}")
    print("\nFirst chunk:")
    print(result[0])
    