"""
Views for the weatherstation APIs.
"""
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Sensor
from weatherstation import serializers


class SensorViewSet(viewsets.ModelViewSet):
    """View for manage Sensor APIs."""
    serializer_class = serializers.SensorSerializer
    queryset = Sensor.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_query_set(self):
        """Retrieve sensors for authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by("-id")

    def perform_create(self, serializer):
        """Create a new sensor."""
        serializer.save(user=self.request.user)
