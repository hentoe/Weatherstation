"""
Tests for location APIs.
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Location

from weatherstation.serializers import LocationSerializer

LOCATION_URL = reverse("weatherstation:location-list")


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicLocationApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving locations."""
        res = self.client.get(LOCATION_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateLocationApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email="user@example.com", password="testp1235")
        self.client.force_authenticate(self.user)

    def test_retrieve_locations(self):
        """Test retrieving a list of locations."""
        Location.objects.create(user=self.user, name="Living Room")
        Location.objects.create(user=self.user, name="Temperature")

        res = self.client.get(LOCATION_URL)

        locations = Location.objects.all().order_by("-name")
        serializer = LocationSerializer(locations, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_sensor_types_limited_to_user(self):
        """Test list of sensor types is limited to authenticated user."""
        user2 = create_user(email="user2@example.com", password="asdfasdf")
        Location.objects.create(user=user2, name="Humidity")
        location = Location.objects.create(
            user=self.user, name="Temperature")

        res = self.client.get(LOCATION_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], location.name)
        self.assertEqual(res.data[0]["id"], location.id)
