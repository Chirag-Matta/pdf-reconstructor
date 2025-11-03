# pdf_utils.py
from PyPDF2 import PdfReader, PdfWriter
from typing import List
import io

def reorder_pdf_bytes(input_bytes: bytes, page_order: List[int]) -> bytes:
    reader = PdfReader(io.BytesIO(input_bytes))
    writer = PdfWriter()
    for idx in page_order:
        writer.add_page(reader.pages[idx])
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()
