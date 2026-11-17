import os
import tempfile
import unittest
import zipfile

from docx import Document

from analyzer.docx_reader import (
    DocxReadError,
    MAX_UNPACKED_SIZE,
    extract_docx_text,
)


class DocxReaderTests(unittest.TestCase):

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.folder.cleanup()

    def path(self, name):
        return os.path.join(self.folder.name, name)

    def test_extracts_paragraphs_in_order(self):
        document = Document()
        document.add_paragraph("Jane Doe")
        document.add_paragraph("SKILLS")
        document.add_paragraph("Python, Flask")
        document.save(self.path("a.docx"))

        text = extract_docx_text(self.path("a.docx"))

        self.assertEqual(text, "Jane Doe\nSKILLS\nPython, Flask\n")

    def test_table_text_stays_between_surrounding_paragraphs(self):
        document = Document()
        document.add_paragraph("SKILLS")
        table = document.add_table(rows=1, cols=2)
        table.rows[0].cells[0].text = "Python"
        table.rows[0].cells[1].text = "SQL"
        document.add_paragraph("EDUCATION")
        document.save(self.path("a.docx"))

        lines = extract_docx_text(self.path("a.docx")).split("\n")

        self.assertEqual(lines[:4], ["SKILLS", "Python", "SQL", "EDUCATION"])

    def test_merged_cells_are_not_repeated(self):
        document = Document()
        table = document.add_table(rows=1, cols=2)
        merged = table.rows[0].cells[0].merge(table.rows[0].cells[1])
        merged.text = "Only once"
        document.save(self.path("a.docx"))

        text = extract_docx_text(self.path("a.docx"))

        self.assertEqual(text.count("Only once"), 1)

    def test_header_text_is_included(self):
        document = Document()
        document.sections[0].header.paragraphs[0].text = "jane@example.com"
        document.add_paragraph("Body text")
        document.save(self.path("a.docx"))

        text = extract_docx_text(self.path("a.docx"))

        self.assertTrue(text.startswith("jane@example.com"))
        self.assertIn("Body text", text)

    def test_empty_document_gives_blank_text(self):
        Document().save(self.path("a.docx"))

        self.assertEqual(extract_docx_text(self.path("a.docx")).strip(), "")

    def test_plain_text_file_is_rejected(self):
        with open(self.path("fake.docx"), "w") as file:
            file.write("this is not a word document")

        with self.assertRaises(DocxReadError):
            extract_docx_text(self.path("fake.docx"))

    def test_zip_without_word_document_is_rejected(self):
        with zipfile.ZipFile(self.path("other.docx"), "w") as archive:
            archive.writestr("hello.txt", "hi")

        with self.assertRaises(DocxReadError):
            extract_docx_text(self.path("other.docx"))

    def test_oversized_unpacked_file_is_rejected(self):
        with zipfile.ZipFile(
            self.path("bomb.docx"), "w", zipfile.ZIP_DEFLATED
        ) as archive:
            archive.writestr("word/document.xml", "<a/>")
            archive.writestr("big.bin", b"0" * (MAX_UNPACKED_SIZE + 1))

        with self.assertRaises(DocxReadError):
            extract_docx_text(self.path("bomb.docx"))


if __name__ == "__main__":
    unittest.main()