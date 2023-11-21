"""
Views for the weatherstation APIs.
"""
from django.db.models import Max

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
from rest_framework.exceptions import ValidationError
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
        try:
            return [int(str_id) for str_id in qs.split(",")]
        except ValueError:
            raise ValidationError(
                {"message": "All parameters need to be integers."})

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
            ),
            OpenApiParameter(
                "latest",
                OpenApiTypes.INT, enum=[0, 1],
                description=("Return only the latest measurement for each "
                             "sensor. If used with start_date and end_date, "
                             "returns the latest measurement within the "
                             "time range "),
            )
        ]
    )
)
class MeasurementViewSet(viewsets.ModelViewSet):
    """View for managing measurement APIs."""
    serializer_class = serializers.MeasurementSerializer
    queryset = Measurement.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _params_to_ints(self, qs):
        """Convert a list of strings to integers."""
        try:
            return [int(str_id) for str_id in qs.split(",")]
        except ValueError:
            raise ValidationError(
                {"message": "All parameters need to be integers."})

    def get_queryset(self):
        """Retrieve measurements for authenticated user."""
        sensors = self.request.query_params.get("sensors")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        latest = self.request.query_params.get("latest", 0)
        if not str(latest).isdigit():
            raise ValidationError(
                {"message": "The 'latest' parameter must be an integer."})
        latest = bool(int(latest))

        queryset = self.queryset

        if sensors:
            sensor_ids = self._params_to_ints(sensors)
            queryset = queryset.filter(sensor__id__in=sensor_ids)

        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)

        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        if latest:
            # Get the latest timestamp for each sensor
            latest_measurements = queryset.values('sensor').annotate(
                latest_timestamp=Max('timestamp'))

            # Filter the queryset to include only the latest measurements
            queryset = queryset.filter(
                sensor__in=[item['sensor'] for item in latest_measurements],
                timestamp__in=[item['latest_timestamp']
                               for item in latest_measurements]
            )

        return queryset.filter(
            user=self.request.user
        ).order_by("-id").distinct()

    def get_serializer_class(self):
        """Return the serializer class for requests."""
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


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                "assigned_only",
                OpenApiTypes.INT, enum=[0, 1],
                description="Filter by items assigned to sensors.",
            )
        ]
    )
)
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

        assigned_only = self.request.query_params.get("assigned_only", 0)
        if not str(assigned_only).isdigit():
            raise ValidationError(
                {"message": "The 'assigned_only' parameter must be an integer."})
        assigned_only = bool(int(assigned_only))

        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(sensor__isnull=False)
        return queryset.filter(
            user=self.request.user
        ).order_by("-name").distinct()

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
