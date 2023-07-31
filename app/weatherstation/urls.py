"""
URLs for the weatherstation app.
"""
from django.urls import (
    include,
    path,
)

from rest_framework.routers import DefaultRouter

from weatherstation import views

router = DefaultRouter()
router.register("sensors", views.SensorViewSet)

app_name = "weatherstation"

urlpatterns = [
    path("", include(router.urls)),
]
