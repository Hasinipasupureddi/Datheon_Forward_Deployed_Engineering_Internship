"""Load supported PDF, CSV, and Markdown files as plain text."""

import csv
from pathlib import Path
from document_reader import read_pdf  # Imports the PDF reader

def read_csv(file_path):
    """Read a CSV file into a list of dictionaries keyed by column name."""
    file_path = Path(file_path)  # Converts the path into a Path object

    records = []  # Stores CSV records

    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)  # Reads rows using column names

        for row in reader:
            records.append(row)  # Adds each row to the records list

    return records

def read_markdown(file_path):
    """Read a Markdown file without altering its source text."""
    file_path = Path(file_path)  # Converts the path into a Path object

    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read()  # Reads the Markdown content

    return text

def load_document(file_path):
    """Dispatch a supported file path to its format-specific reader."""
    file_path = Path(file_path)  # Converts the path into a Path object

    extension = file_path.suffix.lower()  # Gets the file extension

    if extension == ".pdf":
        return read_pdf(file_path)  # Reads PDF files

    elif extension == ".csv":
        records = read_csv(file_path)  # Reads CSV records
        return "\n".join(
            " | ".join(f"{key}: {value}" for key, value in record.items())
            for record in records
        )  # Converts CSV records into text

    elif extension == ".md":
        return read_markdown(file_path)  # Reads Markdown files

    else:
        raise ValueError("Unsupported file format")


if __name__ == "__main__":
    files = [
        "data/raw/sample.pdf",
        "data/raw/sample.csv",
        "data/raw/sample.md"
    ]

    for file_path in files:
        content = load_document(file_path)

        print(f"\nFile: {file_path}")
        print(content[:500])