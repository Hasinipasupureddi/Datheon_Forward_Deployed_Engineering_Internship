"""Extract text from PDFs, using OCR when a PDF has no text layer."""

import os
import shutil
from pathlib import Path

import pytesseract
from pdf2image import convert_from_path
from pypdf import PdfReader


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


def read_pdf(file_path):
    """Return all PDF text, falling back to Tesseract for scanned pages."""
    reader = PdfReader(file_path)
    text = ""

    for page in reader.pages:
        text += page.extract_text() or ""

    if text.strip():
        return text

    print("Scanned PDF detected. Starting OCR...")

    conversion_options = {}
    if POPPLER_PATH:
        conversion_options["poppler_path"] = POPPLER_PATH

    images = convert_from_path(
        str(file_path),
        **conversion_options
    )

    for image in images:
        text += pytesseract.image_to_string(image)

    return text


def save_text(text, output_path):
    """Write extracted text to a UTF-8 file, creating parent directories."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        file.write(text)

    print(f"Text saved successfully: {output_path}")


if __name__ == "__main__":
    input_path = "data/raw/sample1.pdf"
    content = read_pdf(input_path)

    if content.strip():
        output_path = "data/processed/sample1.txt"
        save_text(content, output_path)
    else:
        print("No text could be extracted.")
