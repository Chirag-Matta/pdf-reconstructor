# pdf_svc.py
from PyPDF2 import PdfReader, PdfWriter
from typing import List
import io
import fitz  # PyMuPDF
from rich import print
from .ocr_svc import ocr_page

def reorder_pdf_bytes(input_bytes: bytes, page_order: List[int]) -> bytes:
    reader = PdfReader(io.BytesIO(input_bytes))
    writer = PdfWriter()
    for idx in page_order:
        writer.add_page(reader.pages[idx])
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()

def extract_text_from_page(page) -> str:
    """Try to extract text natively from the page; if empty, try OCR on the page image."""
    txt = page.get_text("text")
    if txt and txt.strip():
        return txt.strip()

    # Fallback: render page to an image and OCR
    return ocr_page(page)

def extract_texts_from_pdf_bytes(pdf_bytes: bytes) -> List[str]:
    """Return list of page texts in order of stored pages (shuffled input expected)."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages_texts = []
    for i in range(doc.page_count):
        page = doc.load_page(i)
        txt = extract_text_from_page(page)
        pages_texts.append(txt)
    doc.close()
    return pages_texts
