"""
Tests for models.
"""
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


def create_user(email="user@example.com", password="password1"):
    """Create and return a new user."""
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):
    """Test models."""

    def test_create_user_with_email_successful(self):
        """Test creating a user with an email is successful."""
        email = "test@example.com"
        password = "testpass123"
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test email is normalized for new users."""
        sample_emails = [
            ["test1@EXAMPLE.com", "test1@example.com"],
            ["Test2@Example.com", "Test2@example.com"],
            ["TEST3@EXAMPLE.com", "TEST3@example.com"],
            ["test4@example.COM", "test4@example.com"],
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, "sample123")
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """Test that creating a user without an email raises a ValueError."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user("", "test123")

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = get_user_model().objects.create_superuser(
            "test@example.com",
            "test123",
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_sensor(self):
        """Test creating a sensor."""
        user = create_user()
        sensor = models.Sensor.objects.create(
            user=user,
            name="Temperature in Magrathea",
            description="Sample description"
        )

        self.assertEqual(str(sensor), sensor.name)

    def test_create_measurement(self):
        """Test creating a measurement."""
        user = create_user()
        sensor = models.Sensor.objects.create(
            user=user,
            name="BME280",
        )
        measurement = models.Measurement.objects.create(
            user=user,
            sensor=sensor,
            value=Decimal("24.5"),
        )

        self.assertEqual(measurement.user.id, user.id)

    def test_create_location(self):
        """Test creating a location."""
        user = create_user()
        location = models.Location.objects.create(
            user=user,
            name="Magrathea"
        )
        self.assertEqual(str(location), location.name)

    def test_create_sensor_type(self):
        """Test creating a sensor type."""
        user = create_user()
        sensor_type = models.SensorType.objects.create(
            user=user,
            name="Temperature",
            unit="Celsius"
        )
        self.assertEqual(str(sensor_type), sensor_type.name)
