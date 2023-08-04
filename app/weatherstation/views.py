"""
Views for the weatherstation APIs.
"""
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)
from rest_framework import status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import (
    Sensor,
    Measurement
)
from weatherstation import serializers


class SensorViewSet(viewsets.ModelViewSet):
    """View for managing sensor APIs."""
    serializer_class = serializers.SensorDetailSerializer
    queryset = Sensor.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve sensors for authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by("-id")

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == "list":
            return serializers.SensorSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new sensor."""
        serializer.save(user=self.request.user)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                "sensors",
                OpenApiTypes.STR,
                description="Comma separated list of sensor IDs to filter",
            )
        ]
    )
)
class MeasurementViewSet(viewsets.ModelViewSet):
    """View for managing measurement APIs."""
    serializer_class = serializers.MeasurementDetailSerializer
    queryset = Measurement.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _params_to_ints(self, qs):
        """Convert a list of strings to integers."""
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        """Retrieve measurements for authenticated user."""
        sensors = self.request.query_params.get("sensors")
        queryset = self.queryset
        if sensors:
            sensor_ids = self._params_to_ints(sensors)
            queryset = queryset.filter(sensor__id__in=sensor_ids)
        return queryset.filter(
            user=self.request.user
        ).order_by("-id").distinct()

    def get_serializer_class(self):
        """Return the serializer class for requests."""
        if self.action == "list":
            return serializers.MeasurementSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new measurement."""
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        """Update a measurement."""
        for k, v in request.data.items():
            if k == "sensor":
                try:
                    sensor = Sensor.objects.get(id=v)
                except Sensor.DoesNotExist:
                    return Response(
                        f"Invalid pk \"{v}\" - Object does not exist.",
                        status.HTTP_400_BAD_REQUEST)
                if sensor.user != request.user:
                    return Response(
                        f"Invalid pk \"{v}\" - Object does not exist.",
                        status.HTTP_400_BAD_REQUEST)

        return super().update(request, *args, **kwargs)
