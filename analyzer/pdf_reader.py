
from pypdf import PdfReader

from analyzer.section_detector import extract_sections


def extract_pdf_text(filepath):

    reader = PdfReader(filepath)

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


def extract_pdf_sections(filepath):
    """Extract text from a PDF and return organized resume sections."""
    text = extract_pdf_text(filepath)
    return extract_sections(text)

