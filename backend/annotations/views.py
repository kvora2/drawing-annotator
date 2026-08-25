from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import Annotation, Document
from .serializers import AnnotationSerializer, DocumentSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all().order_by("-created_at")
    serializer_class = DocumentSerializer

    def create(self, request, *args, **kwargs):
        """Accept a PDF upload, save it, then rasterize its pages."""
        upload = request.FILES.get("file")
        if upload is None:
            return Response({"detail": "No file provided under key 'file'."},
                            status=status.HTTP_400_BAD_REQUEST)

        doc = Document.objects.create(name=upload.name, file=upload)
        try:
            doc.num_pages = services.render_document_pages(doc)
            doc.save(update_fields=["num_pages"])
        except Exception as exc:  # noqa: BLE001 - surface render errors to the client
            doc.delete()
            return Response({"detail": f"Could not render PDF: {exc}"},
                            status=status.HTTP_400_BAD_REQUEST)

        ser = self.get_serializer(doc)
        return Response(ser.data, status=status.HTTP_201_CREATED)


class AnnotationViewSet(viewsets.ModelViewSet):
    serializer_class = AnnotationSerializer

    def get_queryset(self):
        qs = Annotation.objects.all()
        document = self.request.query_params.get("document")
        page = self.request.query_params.get("page")
        if document:
            qs = qs.filter(document_id=document)
        if page:
            qs = qs.filter(page=page)
        return qs

    @action(detail=True, methods=["post"])
    def ocr(self, request, pk=None):
        """Run local OCR on this annotation's region and persist the text."""
        ann = self.get_object()
        if ann.kind != Annotation.CAPTURE:
            return Response({"detail": "OCR only applies to capture (green) boxes."},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            ann.text = services.ocr_region(ann.document, ann.page, ann.x, ann.y, ann.w, ann.h)
        except Exception as exc:  # noqa: BLE001
            return Response({"detail": f"OCR failed: {exc}"},
                            status=status.HTTP_400_BAD_REQUEST)
        ann.save(update_fields=["text", "updated_at"])
        return Response(AnnotationSerializer(ann).data)
