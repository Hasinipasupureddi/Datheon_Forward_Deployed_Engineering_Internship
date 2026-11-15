from __future__ import annotations

from pathlib import Path
from typing import Optional
import csv


def _default_processed_dir() -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    return repo_root / "data" / "processed"


def save_text_output(text: str, source_path: str | Path, output_dir: Optional[str | Path] = None) -> Path:
    """Save extracted text to data/processed as a .txt file."""
    source = Path(source_path)
    destination_dir = Path(output_dir) if output_dir else _default_processed_dir()
    destination_dir.mkdir(parents=True, exist_ok=True)

    destination_path = destination_dir / f"{source.stem}.txt"
    destination_path.write_text(text, encoding="utf-8")
    return destination_path


def extract_pdf_text(file_path: str | Path) -> str:
    """Extract text from a PDF using pypdf."""
    from pypdf import PdfReader

    reader = PdfReader(str(file_path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages).strip()


def extract_csv_text(file_path: str | Path) -> str:
    """Extract CSV content as readable rows using pandas when available."""
    try:
        import pandas as pd
    except ModuleNotFoundError:
        with open(file_path, "r", encoding="utf-8", newline="") as csv_file:
            reader = csv.reader(csv_file)
            rows = [",".join(row) for row in reader]
        return "\n".join(rows).strip() + "\n"

    dataframe = pd.read_csv(file_path)
    return dataframe.to_csv(index=False)


def extract_markdown_text(file_path: str | Path) -> str:
    """Load Markdown content as plain text."""
    return Path(file_path).read_text(encoding="utf-8")


def ingest_document(file_path: str | Path, output_dir: Optional[str | Path] = None) -> Path:
    """Ingest PDF, CSV, or Markdown, then save extracted text into .txt file."""
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        text = extract_pdf_text(path)
    elif suffix == ".csv":
        text = extract_csv_text(path)
    elif suffix in {".md", ".markdown"}:
        text = extract_markdown_text(path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    return save_text_output(text, source_path=path, output_dir=output_dir)
