
# Enterprise AI Document Assistant
### Automated Data Extraction and Embedding Pipeline

## 1. Project Overview

The Enterprise AI Document Assistant is an automated document processing and semantic search system developed as part of the Datheon Forward Deployed Engineering Internship.

It extracts information from PDF, CSV, and Markdown files, performs OCR on scanned PDFs, divides documents into meaningful chunks, preserves metadata, generates embeddings, and stores them in ChromaDB.

Users can search documents using natural-language queries and retrieve relevant information through semantic similarity and metadata filtering.

## 2. Problem Statement

Organizations maintain large amounts of information in different document formats.

Manually searching these documents is time-consuming. Scanned PDFs also create difficulties because their content may not be directly extractable.

This project provides an automated pipeline to:

- Process multiple document formats.
- Extract text from normal and scanned PDFs.
- Divide text into meaningful chunks.
- Preserve document metadata.
- Generate and store text embeddings.
- Retrieve relevant information using semantic search.
- Filter search results using access tiers and departments.

## 3. Project Architecture

```text
PDF / CSV / Markdown
        |
        v
Document Extraction and OCR
        |
        v
Semantic Chunking
        |
        v
Metadata Attachment
        |
        v
MiniLM Embeddings
        |
        v
ChromaDB Vector Storage
        |
        v
Semantic Search
        |
        v
Metadata Filtering and Results
```

## 4. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| pypdf | PDF text extraction |
| pdf2image | Converts PDF pages into images |
| Tesseract OCR | Extracts text from scanned images |
| pytesseract | Python interface for Tesseract |
| ChromaDB | Persistent vector database |
| MiniLM | Generates text embeddings |
| Cosine similarity | Similarity-based comparison |

## 5. Project Structure

```text
Datheon_Forward_Deployed_Engineering_Internship/
|
|-- data/
|   |-- raw/
|   |   |-- sample.csv
|   |   |-- sample.md
|   |
|   |-- processed/
|   |-- chroma_db/ (generated locally)
|
|-- src/
|   |-- document_reader.py
|   |-- multi_format_reader.py
|   |-- chunker.py
|   |-- ingest.py
|   |-- vector_store.py
|   |-- main.py
|
|-- tests/
|   |-- test_pipeline.py
|
|-- .gitignore
|-- requirements.txt
|-- README.md
```

Note: The scanned and regular PDF files used during local testing are private class notes and are not included in this public repository.

## 6. Implementation Steps

### Step 1: PDF Text Extraction and OCR

Implemented PDF text extraction using pypdf.

When a PDF contains no extractable text, its pages are converted into images using pdf2image.

Tesseract OCR then recognizes text from the images.

### Step 2: Multi-format Document Reading

Implemented a common document loader to support:

- PDF files
- CSV files
- Markdown files

CSV files are read using Python's csv.DictReader. Markdown files are read as text.

### Step 3: Semantic Chunking

Documents are divided into smaller chunks.

The paragraph-based chunker was upgraded to use MiniLM embeddings and cosine similarity.

Related paragraphs are grouped based on their similarity, while less-related paragraphs can be separated.

The current similarity threshold is 0.35, and the configured chunk-size threshold is 800 characters.

The chunk-size threshold is a grouping limit; an individual paragraph longer than the threshold is not explicitly split.

### Step 4: Metadata Preservation

Each chunk is associated with metadata such as:

- Department
- Access tier
- Ingestion date
- File type
- Chunk index

Unique chunk IDs are generated using the source filename and chunk position.

### Step 5: Vector Database Storage

ChromaDB is used as a persistent vector database.

Text chunks are converted into embeddings and stored along with their IDs and metadata.

The collection uses cosine distance for similarity search.

Batch insertion and updating are performed using upsert.

### Step 6: Semantic Search

Users can search documents using natural-language queries.

The query is converted into an embedding, and ChromaDB retrieves relevant document chunks based on similarity.

### Step 7: Metadata Filtering

Search results can be filtered using access tiers and department metadata.

The implementation demonstrates metadata-based access filtering.

This is a prototype filtering mechanism, not a complete production authentication and authorization system. In production, permissions should be derived from the authenticated user on the server side.

### Step 8: Testing and Benchmarking

The pipeline was tested using PDF, scanned PDF, CSV, and Markdown sample documents.

Access-tier filtering and department filtering were also tested.

Processing, storage, and search execution times were measured using Python's time.perf_counter().

## 7. Benchmark Results

The following results were recorded during one local execution using all four test documents, including private PDF test files.

| Metric | Result |
|---|---:|
| Total chunks generated | 261 |
| Database records | 261 |
| Document ingestion time | 298.2806 seconds |
| Embedding and storage time | 7.3007 seconds |
| Semantic search time | 0.3163 seconds |

### Document Processing Results

| Input file | Chunks |
|---|---:|
| sample.csv | 1 |
| sample.md | 2 |
| sample.pdf | 56 |
| sample1.pdf | 202 |
| Total | 261 |

### Access Filtering Results

| Access tier | Chunks |
|---|---:|
| Internal | 56 |
| Confidential | 202 |
| Public | 3 |
| Total | 261 |

All access-filtering tests passed during local testing.

Note:
- The PDF test documents used for these benchmark results are private class notes and are not included in this repository.
- Benchmark values are from one recorded execution and may vary depending on hardware, document size, and OCR processing time.
- The public sample files can be used to run the pipeline, but the exact benchmark figures above may not be reproduced without the original PDF test files.

## 8. Installation and Setup

### Prerequisites

- Python 3.12
- Tesseract OCR
- Poppler

Tesseract OCR and Poppler must be installed separately.

Update their executable paths in `src/document_reader.py` according to your local installation.

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Run the Complete Pipeline

From the project root:

```bash
python src/main.py
```

This executes document ingestion, semantic chunking, metadata attachment, vector storage, search, and benchmarking.

### Run Tests

From the project root, use PowerShell:

```powershell
$env:PYTHONPATH="src"
python tests/test_pipeline.py
```

## 9. Key Achievements

- Multi-format document ingestion.
- Scanned PDF text extraction using OCR.
- Similarity-based semantic chunking.
- Metadata preservation.
- Persistent ChromaDB storage.
- Cosine-distance semantic search.
- Metadata-based access filtering.
- Batch ingestion and performance benchmarking.

## 10. Future Enhancements

- Support additional document formats.
- Improve semantic chunking and evaluate similarity thresholds.
- Add configurable batch processing.
- Implement authenticated user access and server-side authorization.
- Optimize OCR and ingestion performance.
- Develop an interactive document-search interface.

## 11. Conclusion

The project demonstrates an automated document extraction and embedding pipeline that converts different document formats into searchable vector data.

It combines document extraction, OCR, semantic chunking, metadata preservation, vector storage, and semantic search in a single workflow.

The implementation provides a foundation for building an enterprise-oriented AI document assistant.
