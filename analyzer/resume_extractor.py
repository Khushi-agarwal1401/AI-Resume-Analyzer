"""Resume file extraction helpers.

This module provides one extraction entry point for supported resume formats
while keeping the PDF and DOCX implementations independent and reusable.
"""

import os
from typing import Optional, Type

from docx import Document
from pypdf import PdfReader


class UnsupportedFileFormatError(ValueError):
    """Raised when a resume format is not supported by the application."""


def extract_pdf_text(
    filepath: str,
    reader_class: Optional[Type[PdfReader]] = None,
) -> str:
    """Extract text from every page of a PDF file."""
    reader = (reader_class or PdfReader)(filepath)
    text = ""

    try:
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    finally:
        # Ensure file streams opened by PdfReader are explicitly closed
        if hasattr(reader, "close"):
            try:
                reader.close()
            except Exception:
                pass
        stream = getattr(reader, "stream", None)
        if stream and hasattr(stream, "close"):
            try:
                stream.close()
            except Exception:
                pass

    return text


def extract_docx_text(filepath: str) -> str:
    """Extract paragraph and table text from a DOCX file."""
    document = Document(filepath)
    paragraphs = [paragraph.text for paragraph in document.paragraphs]
    tables = [
        "\n".join(
            cell.text
            for row in table.rows
            for cell in row.cells
        )
        for table in document.tables
    ]
    return "\n".join(paragraphs + tables)


def extract_resume_text(filepath: str) -> str:
    """Extract resume text based on the file extension.

    Raises:
        UnsupportedFileFormatError: if the path does not use a supported
            resume extension.
    """
    extension = os.path.splitext(filepath)[1].lower()
    if extension == ".pdf":
        return extract_pdf_text(filepath)
    if extension == ".docx":
        return extract_docx_text(filepath)

    raise UnsupportedFileFormatError("Only PDF and DOCX files are supported.")
