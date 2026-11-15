import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.document_reader import ingest_document, save_text_output


class DocumentReaderTests(unittest.TestCase):
    def test_save_text_output_creates_txt_file(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            output = save_text_output(
                text="hello world",
                source_path="example.md",
                output_dir=tmp_dir,
            )

            self.assertEqual(output.name, "example.txt")
            self.assertEqual(output.read_text(encoding="utf-8"), "hello world")

    def test_ingest_markdown_saves_processed_txt(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            markdown_path = Path(tmp_dir) / "notes.md"
            markdown_path.write_text("# Title\n\ncontent", encoding="utf-8")

            output = ingest_document(markdown_path, output_dir=tmp_dir)

            self.assertTrue(output.exists())
            self.assertEqual(output.name, "notes.txt")
            self.assertEqual(output.read_text(encoding="utf-8"), "# Title\n\ncontent")

    def test_ingest_csv_saves_processed_txt(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            csv_path = Path(tmp_dir) / "table.csv"
            csv_path.write_text("col1,col2\n1,2\n", encoding="utf-8")

            output = ingest_document(csv_path, output_dir=tmp_dir)

            self.assertTrue(output.exists())
            self.assertEqual(output.name, "table.txt")
            self.assertIn("col1,col2", output.read_text(encoding="utf-8"))

    def test_ingest_document_rejects_unsupported_extension(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "unsupported.txt"
            path.write_text("text", encoding="utf-8")

            with self.assertRaises(ValueError):
                ingest_document(path, output_dir=tmp_dir)


if __name__ == "__main__":
    unittest.main()
