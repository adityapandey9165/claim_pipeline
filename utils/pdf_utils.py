import fitz  # PyMuPDF
import base64
from typing import List, Dict


def extract_pages_as_images(pdf_path: str) -> List[Dict]:
    """Extract each PDF page as base64 image + text."""
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        # Render page to image
        mat = fitz.Matrix(1.5, 1.5)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")

        # Also extract text
        text = page.get_text()

        pages.append({
            "page_num": i + 1,
            "image_b64": img_b64,
            "text": text.strip()
        })
    doc.close()
    return pages


def extract_pages_by_indices(all_pages: List[Dict], indices: List[int]) -> List[Dict]:
    """Return only pages matching given page numbers (1-indexed)."""
    return [p for p in all_pages if p["page_num"] in indices]