"""API tests for the drawing annotator.

These cover the existing, working behaviour only. Known validation gaps are
documented in the README ("Known gaps") rather than encoded as failing tests.

Isolation:
- Django's test runner creates a throwaway test database, so db.sqlite3 is untouched.
- Each test class gets its own temporary MEDIA_ROOT, removed when the class finishes,
  so uploaded PDFs and rendered PNGs never land in backend/media.

The capture-OCR test needs the Tesseract binary on PATH and is skipped without it.
"""
import shutil
import tempfile
from pathlib import Path
from unittest import skipUnless

import pymupdf
import pytesseract
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Annotation, Document


def _tesseract_available():
    try:
        pytesseract.get_tesseract_version()
    except Exception:  # noqa: BLE001 - any failure means OCR can't run here
        return False
    return True


TESSERACT_AVAILABLE = _tesseract_available()


def make_pdf_bytes(pages=1):
    """Build a small PDF in memory with large, OCR-friendly text on each page."""
    pdf = pymupdf.open()
    for i in range(1, pages + 1):
        page = pdf.new_page(width=612, height=792)
        page.insert_text((72, 100), f"HELLO PAGE {i}", fontsize=36)
    data = pdf.tobytes()
    pdf.close()
    return data


class IsolatedMediaAPITestCase(APITestCase):
    """APITestCase that points MEDIA_ROOT at a temp dir for the whole class."""

    @classmethod
    def setUpClass(cls):
        media_dir = Path(tempfile.mkdtemp(prefix="annotations-test-media-"))
        # Class cleanups run in reverse order, even if setUpClass fails partway:
        # restore settings first, then delete the directory.
        cls.addClassCleanup(shutil.rmtree, media_dir, ignore_errors=True)
        media_override = override_settings(MEDIA_ROOT=media_dir)
        media_override.enable()
        cls.addClassCleanup(media_override.disable)
        cls.media_root = media_dir
        super().setUpClass()

    def upload_pdf(self, pages=1, name="drawing.pdf", content=None):
        upload = SimpleUploadedFile(
            name, content if content is not None else make_pdf_bytes(pages),
            content_type="application/pdf",
        )
        return self.client.post("/api/documents/", {"file": upload}, format="multipart")

    def create_document(self, pages=1):
        response = self.upload_pdf(pages=pages)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        return response.json()

    def create_annotation(self, document_id, **overrides):
        body = {"document": document_id, "page": 1, "kind": Annotation.CAPTURE,
                "x": 0.05, "y": 0.05, "w": 0.9, "h": 0.12}
        body.update(overrides)
        response = self.client.post("/api/annotations/", body, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        return response.json()


class DocumentUploadTests(IsolatedMediaAPITestCase):
    def test_upload_renders_every_page(self):
        doc = self.create_document(pages=2)

        self.assertEqual(doc["num_pages"], 2)
        self.assertEqual(doc["name"], "drawing.pdf")
        self.assertEqual(len(doc["pages"]), 2)
        self.assertTrue(doc["pages"][1].endswith(f"/media/renders/{doc['id']}/page_2.png"))
        render_dir = self.media_root / "renders" / str(doc["id"])
        self.assertTrue((render_dir / "page_1.png").is_file())
        self.assertTrue((render_dir / "page_2.png").is_file())

    def test_upload_without_file_is_rejected(self):
        response = self.client.post("/api/documents/", {}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Document.objects.count(), 0)

    def test_upload_of_unreadable_pdf_is_rejected_and_not_saved(self):
        response = self.upload_pdf(content=b"definitely not a pdf")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Could not render PDF", response.json()["detail"])
        self.assertEqual(Document.objects.count(), 0)


class AnnotationApiTests(IsolatedMediaAPITestCase):
    def test_annotations_persist_filter_and_delete(self):
        doc_id = self.create_document(pages=2)["id"]
        capture = self.create_annotation(doc_id, page=1, kind=Annotation.CAPTURE)
        self.create_annotation(doc_id, page=2, kind=Annotation.IGNORE)
        other_doc_id = self.create_document(pages=1)["id"]
        self.create_annotation(other_doc_id, page=1)

        # Persisted, and nested in the document detail.
        detail = self.client.get(f"/api/documents/{doc_id}/").json()
        self.assertEqual({a["kind"] for a in detail["annotations"]},
                         {Annotation.CAPTURE, Annotation.IGNORE})

        # Filtering by document, and by document + page.
        by_doc = self.client.get(f"/api/annotations/?document={doc_id}").json()
        self.assertEqual(len(by_doc), 2)
        page_one = self.client.get(f"/api/annotations/?document={doc_id}&page=1").json()
        self.assertEqual([a["id"] for a in page_one], [capture["id"]])
        self.assertEqual(page_one[0]["x"], 0.05)

        # Deletion.
        response = self.client.delete(f"/api/annotations/{capture['id']}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        remaining = self.client.get(f"/api/annotations/?document={doc_id}").json()
        self.assertEqual([a["kind"] for a in remaining], [Annotation.IGNORE])


class OcrTests(IsolatedMediaAPITestCase):
    def setUp(self):
        self.doc_id = self.create_document(pages=1)["id"]

    @skipUnless(TESSERACT_AVAILABLE, "Tesseract binary not found on PATH")
    def test_ocr_on_capture_box_extracts_and_saves_text(self):
        ann = self.create_annotation(self.doc_id, kind=Annotation.CAPTURE)

        response = self.client.post(f"/api/annotations/{ann['id']}/ocr/")

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        self.assertIn("HELLO", response.json()["text"].upper())
        self.assertIn("HELLO", Annotation.objects.get(pk=ann["id"]).text.upper())

    def test_ocr_on_ignore_box_is_rejected(self):
        ann = self.create_annotation(self.doc_id, kind=Annotation.IGNORE)

        response = self.client.post(f"/api/annotations/{ann['id']}/ocr/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Annotation.objects.get(pk=ann["id"]).text, "")
