# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    ProjectViewSet,
    FormSchemaViewSet,
    FormSubmissionViewSet,
    TableConfigViewSet,
    GraphConfigViewSet,
    GraphDataView,
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'projects', ProjectViewSet)
router.register(r'formschemas', FormSchemaViewSet)
router.register(r'formsubmissions', FormSubmissionViewSet)
router.register(r'tableconfigs', TableConfigViewSet)
router.register(r'graphconfigs', GraphConfigViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/graph-data/<int:graph_id>/', GraphDataView.as_view(), name='graph-data'),
]
