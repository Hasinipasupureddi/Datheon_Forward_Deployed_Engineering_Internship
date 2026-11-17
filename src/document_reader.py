
from pypdf import PdfReader
import pytesseract
from pdf2image import convert_from_path
from pathlib import Path

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def read_pdf(file_path):
    reader = PdfReader(file_path)

    text = ""

    for page in reader.pages:
        text += page.extract_text() or ""

    if text.strip():
        return text

    print("Scanned PDF detected. Starting OCR...")

    images = convert_from_path(
        file_path,
        poppler_path=r"C:\poppler\poppler-26.09.0\Library\bin"
    )
    for image in images:
        text += pytesseract.image_to_string(image)

    return text

def save_text(text, output_path):
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
