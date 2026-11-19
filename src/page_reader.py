"""Read PDF pages while retaining page numbers for citations."""

import os
import shutil
from pathlib import Path

import pytesseract
from pypdf import PdfReader
from pdf2image import convert_from_path


WINDOWS_TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
WINDOWS_POPPLER = r"C:\poppler\poppler-26.09.0\Library\bin"

tesseract_path = os.getenv("TESSERACT_CMD") or (
    WINDOWS_TESSERACT if Path(WINDOWS_TESSERACT).exists()
    else shutil.which("tesseract")
)

if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

POPPLER_PATH = os.getenv("POPPLER_PATH") or (
    WINDOWS_POPPLER if Path(WINDOWS_POPPLER).exists()
    else None
)


def read_pdf_pages(file_path):
    """Return page dictionaries and use OCR when the PDF has no text layer."""
    file_path = Path(file_path)
    reader = PdfReader(file_path)

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append({
            "page_number": page_number,
            "content": text.strip()
        })

    if any(page["content"] for page in pages):
        return pages

    print("Scanned PDF detected. Starting OCR...")

    conversion_options = {}
    if POPPLER_PATH:
        conversion_options["poppler_path"] = POPPLER_PATH

    images = convert_from_path(
        str(file_path),
        **conversion_options
    )

    pages = []

    for page_number, image in enumerate(images, start=1):
        text = pytesseract.image_to_string(image)
        pages.append({
            "page_number": page_number,
            "content": text.strip()
        })

    return pages
