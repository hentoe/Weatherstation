"""Serializers for weatherstation APIs."""
from rest_framework import serializers

from core.models import (
    Location,
    Measurement,
    Sensor,
    SensorType,
)


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


class MeasurementSerializer(serializers.ModelSerializer):
    """Serializer for Measurements."""

    class Meta:
        model = Measurement
        fields = ["id", "timestamp", "value"]
        read_only_fields = ["id", "timestamp"]


class MeasurementDetailSerializer(MeasurementSerializer):
    """Serializer for measurement detail view."""

    class Meta(MeasurementSerializer.Meta):
        fields = MeasurementSerializer.Meta.fields + ["sensor"]


class SensorTypeSerializer(serializers.ModelSerializer):
    """Serializer for SensorTypes."""

    class Meta:
        model = SensorType
        fields = ["id", "name", "unit"]
        read_only_fields = ["id"]


class LocationSerializer(serializers.ModelSerializer):
    """Serializer for Locations."""

    class Meta:
        model = Location
        fields = ["id", "name"]
        read_only_fields = ["id"]
