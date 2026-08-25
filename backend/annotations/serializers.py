from rest_framework import serializers

from .models import Annotation, Document


class AnnotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Annotation
        fields = ["id", "document", "page", "kind", "x", "y", "w", "h", "text",
                  "created_at", "updated_at"]
        read_only_fields = ["text", "created_at", "updated_at"]


class DocumentSerializer(serializers.ModelSerializer):
    pages = serializers.SerializerMethodField()
    annotations = AnnotationSerializer(many=True, read_only=True)

    class Meta:
        model = Document
        fields = ["id", "name", "num_pages", "pages", "annotations", "created_at"]

    def get_pages(self, obj):
        """Absolute URLs to each rendered page image, in order."""
        request = self.context.get("request")
        urls = []
        for i in range(1, obj.num_pages + 1):
            path = f"{obj.id}/page_{i}.png"
            url = f"/media/renders/{path}"
            urls.append(request.build_absolute_uri(url) if request else url)
        return urls
