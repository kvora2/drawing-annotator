from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path("api/", include("annotations.urls")),
]

# Serve uploaded PDFs and rendered page images during development.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
