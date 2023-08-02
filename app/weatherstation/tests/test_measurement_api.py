"""
Tests for measurement APIs.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Measurement

from weatherstation.serializers import MeasurementSerializer
from weatherstation.tests.test_sensor_api import create_sensor


MEASUREMENTS_URL = reverse("weatherstation:measurement-list")


def create_measurement(user, sensor, **params):
    """Create and return a sample measurement"""
    defaults = {
        "value": Decimal("24"),
    }
    defaults.update(params)

    measurement = Measurement.objects.create(
        user=user, sensor=sensor, **defaults)
    return measurement


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicMeasurementAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(MEASUREMENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateMeasurementAPITests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email="user@example.com", password="testp1235")
        self.client.force_authenticate(self.user)

    def test_retrieve_measurements(self):
        """Test retrieving a list of measurements."""
        sensor = create_sensor(user=self.user)
        create_measurement(user=self.user, sensor=sensor)
        create_measurement(user=self.user, sensor=sensor)
        create_measurement(user=self.user, sensor=sensor)

        res = self.client.get(MEASUREMENTS_URL)

        measurements = Measurement.objects.all().order_by("-id")
        serializer = MeasurementSerializer(measurements, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_measurement_list_limited_to_user(self):
        """Test list of measurements is limited to authenticated user."""
        other_user = create_user(
            email="user2@example.com", password="löaksdjfa")
        other_sensor = create_sensor(user=other_user)
        sensor = create_sensor(user=self.user)
        create_measurement(user=other_user, sensor=other_sensor)
        create_measurement(user=self.user, sensor=sensor)

        res = self.client.get(MEASUREMENTS_URL)

        measurements = Measurement.objects.filter(user=self.user)
        serializer = MeasurementSerializer(measurements, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
