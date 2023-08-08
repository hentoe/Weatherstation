"""Serializers for weatherstation APIs."""
from rest_framework import serializers

from core.models import (
    Location,
    Measurement,
    Sensor,
    SensorType,
)


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


class SensorSerializer(serializers.ModelSerializer):
    """Serializer for sensors."""
    sensor_type = SensorTypeSerializer(required=False)
    location = LocationSerializer(required=False)

    class Meta:
        model = Sensor
        fields = ["id", "name", "sensor_type", "location"]
        read_only_fields = ["id"]

    def _get_or_create_sensor_type(self, sensor_type, sensor):
        """Handle getting or creating a sensor type."""
        auth_user = self.context["request"].user
        if sensor_type:
            sensor_type_obj, created = SensorType.objects.get_or_create(
                user=auth_user,
                **sensor_type
            )
            sensor.sensor_type = sensor_type_obj

    def _get_or_create_location(self, location, sensor):
        """Handle getting or creating a location."""
        auth_user = self.context["request"].user
        if location:
            location_obj, created = Location.objects.get_or_create(
                user=auth_user,
                **location
            )
            sensor.location = location_obj

    def create(self, validated_data):
        """Create a sensor."""
        sensor_type = validated_data.pop("sensor_type", None)
        location = validated_data.pop("location", None)
        sensor = Sensor.objects.create(**validated_data)
        self._get_or_create_sensor_type(sensor_type, sensor)
        self._get_or_create_location(location, sensor)

        sensor.save()
        return sensor


class SensorDetailSerializer(SensorSerializer):
    """Serializer for sensor detail view."""

    class Meta(SensorSerializer.Meta):
        fields = SensorSerializer.Meta.fields + \
            ["description"]


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
