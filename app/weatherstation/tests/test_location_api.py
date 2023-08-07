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


def detail_url(location_id):
    """Create and return a location detail URL."""
    return reverse("weatherstation:location-detail", args=[location_id])


def create_location(user, **params):
    """Create and return a sample location."""
    defaults = {"name": "Basement"}
    defaults.update(params)

    location = Location.objects.create(user=user, **defaults)

    return location


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
        create_location(user=self.user, name="Living Room")
        create_location(user=self.user)

        res = self.client.get(LOCATION_URL)

        locations = Location.objects.all().order_by("-name")
        serializer = LocationSerializer(locations, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_location_limited_to_user(self):
        """Test list of locations is limited to authenticated user."""
        user2 = create_user(email="user2@example.com", password="asdfasdf")
        create_location(user=user2, name="Bathroom")
        location = create_location(user=self.user, name="Pool")

        res = self.client.get(LOCATION_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], location.name)
        self.assertEqual(res.data[0]["id"], location.id)

    def test_create_location(self):
        """Test creating a location."""
        payload = {
            "name": "Basement",
        }
        res = self.client.post(LOCATION_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        location = Location.objects.get(id=res.data["id"])
        for k, v in payload.items():
            self.assertEqual(getattr(location, k), v)
        self.assertEqual(location.user, self.user)

    def test_partial_update_location(self):
        """Test partial update of a location."""
        location = create_location(user=self.user)

        payload = {"name": "Room 404"}

        url = detail_url(location.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        location.refresh_from_db()
        self.assertEqual(location.name, payload["name"])

    def test_full_update_location(self):
        """Test full update of a location."""
        location = create_location(user=self.user)

        payload = {"name": "Room 404"}

        url = detail_url(location.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        location.refresh_from_db()
        self.assertEqual(location.name, payload["name"])

    def test_update_user_returns_error(self):
        """Test try changing the user of a location does not change user."""
        new_user = create_user(email="user2@example.com", password="sdklfjohj")
        location = create_location(user=self.user)

        payload = {"user": new_user.id}
        url = detail_url(location.id)
        self.client.patch(url, payload)

        location.refresh_from_db()
        self.assertEqual(location.user, self.user)

    def test_delete_location(self):
        """Test deleting a location."""
        location = create_location(user=self.user)

        url = detail_url(location.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_other_users_location_error(self):
        """Test trying to delete another users location gives error."""
        new_user = create_user(email="user2@example.com",
                               password="alsdkfnalkösdfhj")
        location = create_location(user=new_user)

        url = detail_url(location.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Location.objects.filter(id=location.id).exists())
