"""
Views for the weatherstation APIs.
"""
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)
from rest_framework import (
    mixins,
    status,
    viewsets
)
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import (
    Location,
    Measurement,
    Sensor,
    SensorType
)
from weatherstation import serializers


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                "locations",
                OpenApiTypes.STR,
                description="Comma separated list of location IDs to filter",
            ),
            OpenApiParameter(
                "sensor_types",
                OpenApiTypes.STR,
                description="Comma separated list of sensortype IDs to filter",
            )
        ]
    )
)
class SensorViewSet(viewsets.ModelViewSet):
    """View for managing sensor APIs."""
    serializer_class = serializers.SensorDetailSerializer
    queryset = Sensor.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _params_to_ints(self, qs):
        """Convert a list of strings to integers."""
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        """Retrieve sensors for authenticated user."""
        locations = self.request.query_params.get("locations")
        sensor_types = self.request.query_params.get("sensor_types")
        queryset = self.queryset
        if locations:
            location_ids = self._params_to_ints(locations)
            queryset = queryset.filter(location__id__in=location_ids)
        if sensor_types:
            sensor_type_ids = self._params_to_ints(sensor_types)
            queryset = queryset.filter(sensor_type__id__in=sensor_type_ids)

        return queryset.filter(
            user=self.request.user
        ).order_by("-id").distinct()

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
            ),
            OpenApiParameter(
                "start_date",
                OpenApiTypes.DATETIME,
                description=("Filter measurements after this date and time "
                             "(YYYY-MM-DD HH:MM:SS). Time zone aware format "
                             "is recommended (e.g., "
                             "'2023-08-06 00:00:00+02:00')."),
            ),
            OpenApiParameter(
                "end_date",
                OpenApiTypes.DATETIME,
                description=("Filter measurements before this date and time "
                             "(YYYY-MM-DD HH:MM:SS). Time zone aware format "
                             "is recommended (e.g., "
                             "'2023-08-06 00:00:00+02:00')."),
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
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        queryset = self.queryset

        if sensors:
            sensor_ids = self._params_to_ints(sensors)
            queryset = queryset.filter(sensor__id__in=sensor_ids)

        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)

        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)

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


class BaseSensorAttrViewSet(mixins.ListModelMixin,
                            mixins.CreateModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.DestroyModelMixin,
                            viewsets.GenericViewSet):
    """Manage sensor types."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter queryset to authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by("-name")

    def perform_create(self, serializer):
        """Create a new measurement."""
        serializer.save(user=self.request.user)


class SensorTypeViewSet(BaseSensorAttrViewSet):
    """Manage sensor types."""
    serializer_class = serializers.SensorTypeSerializer
    queryset = SensorType.objects.all()


class LocationViewSet(BaseSensorAttrViewSet):
    """Manage locations."""
    serializer_class = serializers.LocationSerializer
    queryset = Location.objects.all()
