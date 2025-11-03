# ocr_svc.py
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
from typing import List
from rich import print

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

def ocr_page(page) -> str:
    """Perform OCR on a single page image."""
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
