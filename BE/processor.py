# processor.py
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
from typing import List, Tuple
from rich import print

# If Tesseract binary isn't in PATH, set pytesseract.pytesseract.tesseract_cmd = "..."
# e.g. pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

def extract_page_images(page) -> List[Image.Image]:
    """Return list of PIL images extracted from a page (if it has images)."""
    images = []
    for img in page.get_images(full=True):
        xref = img[0]
        pix = fitz.Pixmap(page.parent, xref)
        mode = "RGB" if pix.n < 4 else "RGBA"
        img_bytes = pix.tobytes()
        try:
            pil = Image.frombytes(mode, [pix.width, pix.height], img_bytes)
        except Exception:
            pil = Image.open(io.BytesIO(img_bytes))
        images.append(pil)
        pix = None
    return images

def extract_text_from_page(page) -> str:
    """Try to extract text natively from the page; if empty, try OCR on the page image."""
    txt = page.get_text("text")
    if txt and txt.strip():
        return txt.strip()

    # Fallback: render page to an image and OCR
    try:
        zoom = 2  # improve OCR accuracy
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes))
        ocr_text = pytesseract.image_to_string(img)
        return ocr_text.strip()
    except Exception as e:
        print(f"[red]OCR fallback failed:[/red] {e}")
        return ""

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
