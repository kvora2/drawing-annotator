from rest_framework.routers import DefaultRouter

from .views import AnnotationViewSet, DocumentViewSet

router = DefaultRouter()
router.register("documents", DocumentViewSet)
router.register("annotations", AnnotationViewSet, basename="annotation")

urlpatterns = router.urls
