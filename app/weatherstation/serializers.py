"""Serializers for weatherstation APIs."""
from rest_framework import serializers

from core.models import Sensor


class SensorSerializer(serializers.ModelSerializer):
    """Serializer for sensors."""

    class Meta:
        model = Sensor
        fields = ["id", "name"]
        read_only_fields = ["id"]


class SensorDetailSerializer(SensorSerializer):
    """Serializer for sensor detail view."""

    class Meta(SensorSerializer.Meta):
        fields = SensorSerializer.Meta.fields + ["description"]
