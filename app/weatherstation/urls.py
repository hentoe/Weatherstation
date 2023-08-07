"""
URL mappings for the weatherstation app.
"""
from django.urls import (
    include,
    path,
)

from rest_framework.routers import DefaultRouter

from weatherstation import views

router = DefaultRouter()
router.register("sensors", views.SensorViewSet)
router.register("measurements", views.MeasurementViewSet)
router.register("sensor_types", views.SensorTypeViewSet)
router.register("locations", views.LocationViewSet)

app_name = "weatherstation"

urlpatterns = [
    path("", include(router.urls)),
]
