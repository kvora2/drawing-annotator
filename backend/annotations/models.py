from django.db import models


class Document(models.Model):
    """An uploaded PDF plus the metadata we need to render and navigate it."""
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to="docs/")
    num_pages = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.num_pages} pages)"


class Annotation(models.Model):
    """A single rectangle on one page.

    Coordinates are stored normalized (0..1) relative to the page, so they are
    independent of zoom level and render DPI. That is what lets the frontend
    draw at any zoom and the backend crop the same region at a higher DPI for OCR.
    """
    CAPTURE = "capture"   # green: text we want to keep / OCR
    IGNORE = "ignore"     # red: content to ignore/skip
    KIND_CHOICES = [(CAPTURE, "capture"), (IGNORE, "ignore")]

    document = models.ForeignKey(Document, related_name="annotations", on_delete=models.CASCADE)
    page = models.PositiveIntegerField()  # 1-based page number
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    x = models.FloatField()  # left, 0..1
    y = models.FloatField()  # top, 0..1
    w = models.FloatField()  # width, 0..1
    h = models.FloatField()  # height, 0..1
    text = models.TextField(blank=True, default="")  # OCR result for capture boxes
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["page", "created_at"]

    def __str__(self):
        return f"{self.kind} p{self.page} of doc {self.document_id}"
