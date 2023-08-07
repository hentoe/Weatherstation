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


def detail_url(sensor_type_id):
    """Create and return a sensor type detail URL."""
    return reverse("weatherstation:sensortype-detail", args=[sensor_type_id])


def create_sensor_type(user, **params):
    """Create and return a sample sensor type."""
    defaults = {
        "name": "Temperature",
        "unit": "°C"
    }
    defaults.update(params)
    sensor_type = SensorType.objects.create(user=user, **defaults)

    return sensor_type


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
        create_sensor_type(user=self.user)
        create_sensor_type(user=self.user)

        res = self.client.get(SENSOR_TYPE_URL)

        sensor_types = SensorType.objects.all().order_by("-name")
        serializer = SensorTypeSerializer(sensor_types, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_sensor_types_limited_to_user(self):
        """Test list of sensor types is limited to authenticated user."""
        user2 = create_user(email="user2@example.com", password="asdfasdf")
        create_sensor_type(user=user2, name="Humidity")
        sensor_type = create_sensor_type(user=self.user)

        res = self.client.get(SENSOR_TYPE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], sensor_type.name)
        self.assertEqual(res.data[0]["id"], sensor_type.id)

    def test_create_sensor_type(self):
        """Test creating a sensor type."""
        payload = {
            "name": "Temperature",
            "unit": "°C",
        }
        res = self.client.post(SENSOR_TYPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        sensor_type = SensorType.objects.get(id=res.data["id"])
        for k, v in payload.items():
            self.assertEqual(getattr(sensor_type, k), v)
        self.assertEqual(sensor_type.user, self.user)

    def test_partial_update_sensor_type(self):
        """Test partial update of a sensor type."""
        sensor_type = create_sensor_type(user=self.user)
        name = sensor_type.name

        payload = {
            "unit": "°C",
        }
        url = detail_url(sensor_type.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        sensor_type.refresh_from_db()
        self.assertEqual(sensor_type.name, name)
        self.assertEqual(sensor_type.unit, payload["unit"])
        self.assertEqual(sensor_type.user, self.user)

    def test_full_update_sensor_type(self):
        """Test full update of a sensor type."""
        sensor_type = create_sensor_type(user=self.user)

        payload = {
            "name": "Pressure",
            "unit": "bar"
        }

        url = detail_url(sensor_type.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        sensor_type.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(sensor_type, k), v)

    def test_update_user_returns_error(self):
        """Test try changing the user of a sensor type does not change user."""
        new_user = create_user(email="user2@example.com", password="sdklfjohj")
        sensor_type = create_sensor_type(user=self.user)

        payload = {"user": new_user.id}
        url = detail_url(sensor_type.id)
        self.client.patch(url, payload)

        sensor_type.refresh_from_db()
        self.assertEqual(sensor_type.user, self.user)
