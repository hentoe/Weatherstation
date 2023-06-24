"""
Tests for sensor APIs.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Sensor

from weatherstation.serializers import SensorSerializer

SENSORS_URL = reverse("weatherstation:sensor-list")


def create_sensor(user, **params):
    """Create and return a sample sensor"""
    default = {
        "name": "Sample sensor name",
        "description": "Sample description",
    }
    default.update(params)

    sensor = Sensor.objects.create(user=user, **default)

    return sensor


class PublicSensorAPITests(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = client.get(SENSORS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateSensorAPITests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = self.get_user_model().objects.create(
            user="user@example.com",
            password="password1234"
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_sensors(self):
        """Test retrieving a list of sensors."""
        create_sensor(user=self.user)
        create_sensor(user=self.user)

        res = self.client.get(SENSORS_URL)

        sensors = Sensor.objects.all().order_by("-id")
        serializer = SensorSerializer(sensors, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_sensor_list_limited_to_user(self):
        """Test list of sensors is limited to authenticated user."""
        other_user = get_user_model().objects.create(
            "other@example.com",
            "password1234",
        )
        create_sensor(user=other_user)
        create_sensor(user=self.user)

        res = self.client.get(SENSORS_URL)

        sensors = Sensor.objects.filter(user=self.user)
        serializer = SensorSerializer(sensors, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
