import io

import pymupdf
import pytesseract
from PIL import Image
from django.conf import settings


def render_document_pages(document):
    """Rasterize every page of the document to a PNG for on-screen display.

    Returns the page count. Images land in MEDIA_ROOT/renders/<doc_id>/page_<n>.png.
    """
    src = pymupdf.open(document.file.path)
    out_dir = settings.MEDIA_ROOT / "renders" / str(document.id)
    out_dir.mkdir(parents=True, exist_ok=True)

    zoom = settings.DISPLAY_DPI / 72.0
    matrix = pymupdf.Matrix(zoom, zoom)
    for i, page in enumerate(src, start=1):
        pix = page.get_pixmap(matrix=matrix)
        pix.save(out_dir / f"page_{i}.png")

    count = src.page_count
    src.close()
    return count


def ocr_region(document, page_number, x, y, w, h):
    """Crop a normalized region from a page, render it at OCR_DPI, and OCR it.

    page_number is 1-based. x/y/w/h are normalized (0..1).
    """
    src = pymupdf.open(document.file.path)
    page = src[page_number - 1]
    pw, ph = page.rect.width, page.rect.height

    clip = pymupdf.Rect(x * pw, y * ph, (x + w) * pw, (y + h) * ph)
    zoom = settings.OCR_DPI / 72.0
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    src.close()

    text = pytesseract.image_to_string(img)
    return text.strip()
