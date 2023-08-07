"""
Tests for sensor type APIs.
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import SensorType

from weatherstation.serializers import SensorTypeSerializer

SENSOR_TYPE_URL = reverse("weatherstation:sensortype-list")


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicSensorTypeApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving sensor types."""
        res = self.client.get(SENSOR_TYPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateSensorTypeApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email="user@example.com", password="testp1235")
        self.client.force_authenticate(self.user)

    def test_retrieve_sensor_types(self):
        """Test retrieving a list of sensor types."""
        SensorType.objects.create(user=self.user, name="Temperature")
        SensorType.objects.create(user=self.user, name="Temperature")

        res = self.client.get(SENSOR_TYPE_URL)

        sensor_types = SensorType.objects.all().order_by("-name")
        serializer = SensorTypeSerializer(sensor_types, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_sensor_types_limited_to_user(self):
        """Test list of sensor types is limited to authenticated user."""
        user2 = create_user(email="user2@example.com", password="asdfasdf")
        SensorType.objects.create(user=user2, name="Humidity")
        sensor_type = SensorType.objects.create(
            user=self.user, name="Temperature")

        res = self.client.get(SENSOR_TYPE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], sensor_type.name)
        self.assertEqual(res.data[0]["id"], sensor_type.id)
