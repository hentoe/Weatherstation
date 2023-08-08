"""
Tests for measurement APIs.
"""
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import make_aware

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Measurement

from weatherstation.serializers import (
    MeasurementSerializer,
    MeasurementDetailSerializer
)
from weatherstation.tests.test_sensor_api import create_sensor


MEASUREMENTS_URL = reverse("weatherstation:measurement-list")


def detail_url(measurement_id):
    """Create and return a measurement detail URL."""
    return reverse("weatherstation:measurement-detail", args=[measurement_id])


def create_measurement(user, sensor, **params):
    """Create and return a sample measurement."""
    defaults = {
        "value": Decimal("24"),
    }
    defaults.update(params)

    measurement = Measurement.objects.create(
        user=user, sensor=sensor, **defaults)
    return measurement


def create_measurements(user, days=10):
    """Create and return a list of measurements."""
    s1 = create_sensor(user=user)
    date = make_aware(datetime.now())
    measurements = []
    for day in range(days):
        m = create_measurement(
            user=user,
            sensor=s1,
            value=day,
            timestamp=date - timedelta(days=days-day)
        )
        measurements.append(m)
    return measurements


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

    def test_get_measurement_detail(self):
        """Test get measurement detail."""
        sensor = create_sensor(user=self.user)
        measurement = create_measurement(user=self.user, sensor=sensor)

        url = detail_url(measurement.id)
        res = self.client.get(url)

        serializer = MeasurementDetailSerializer(measurement)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_measurement(self):
        """Test creating a measurement."""
        sensor = create_sensor(user=self.user)

        payload = {
            "value": Decimal("23.5"),
            "sensor": sensor.id,
        }
        res = self.client.post(MEASUREMENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        measurement = Measurement.objects.get(id=res.data["id"])
        for k, v in payload.items():
            if k == "sensor":
                self.assertEqual(getattr(measurement, k).id, v)
            else:
                self.assertEqual(getattr(measurement, k), v)

        self.assertEqual(measurement.user, self.user)

    def test_partial_update(self):
        """Test partial update of a measurement."""
        original_value = Decimal("15.0")
        sensor = create_sensor(user=self.user)
        measurement = create_measurement(
            user=self.user,
            sensor=create_sensor(user=self.user),
            value=original_value
        )

        payload = {"sensor": sensor.id}
        url = detail_url(measurement.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        measurement.refresh_from_db()
        self.assertEqual(measurement.sensor.id, payload["sensor"])
        self.assertEqual(measurement.value, original_value)
        self.assertEqual(measurement.user, self.user)

    def test_full_update(self):
        """Test full update of a measurement."""
        sensor = create_sensor(
            user=self.user,
            name="Test Sensor",
            description="New Description",
        )
        measurement = create_measurement(
            user=self.user,
            sensor=create_sensor(user=self.user))

        payload = {
            "value": Decimal("-1.23"),
            "sensor": sensor.id
        }

        url = detail_url(measurement.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        measurement.refresh_from_db()
        for k, v in payload.items():
            if k == "sensor":
                self.assertEqual(getattr(measurement, k).id, v)
            else:
                self.assertEqual(getattr(measurement, k), v)
        self.assertEqual(measurement.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the measurement user results in an error."""
        new_user = create_user(email="user2@example.com",
                               password="sdklfjölohj")
        sensor = create_sensor(user=self.user)
        measurement = create_measurement(user=self.user, sensor=sensor)

        payload = {"user": new_user.id}
        url = detail_url(measurement.id)
        self.client.patch(url, payload)
        measurement.refresh_from_db()
        self.assertEqual(measurement.user, self.user)

    def test_update_with_other_users_sensor_returns_error(self):
        """
        Test changing the measurement sensor to another users sensor
        results in an error.
        """
        new_user = create_user(email="user2@example.com",
                               password="sdklfjölohj")
        sensor = create_sensor(user=self.user)
        wrong_sensor = create_sensor(user=new_user, name="Wrong Sensor")
        measurement = create_measurement(user=self.user, sensor=sensor)

        payload = {
            "sensor": wrong_sensor.id,
        }
        url = detail_url(measurement.id)
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        measurement.refresh_from_db()
        self.assertEqual(measurement.sensor, sensor)

    def test_update_other_users_measurement_returns_error(self):
        """Test updating another users measurement returns an error."""
        new_user = create_user(email="user2@example.com",
                               password="sdklfjölohj")
        sensor = create_sensor(user=new_user)
        measurement = create_measurement(user=new_user, sensor=sensor)

        payload = {
            "value": Decimal("3.14")
        }
        url = detail_url(measurement.id)

        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        measurement.refresh_from_db()
        self.assertEqual(measurement.user, new_user)

    def test_delete_measurement(self):
        """Test deleting a measurement successful."""
        sensor = create_sensor(user=self.user)
        measurement = create_measurement(user=self.user, sensor=sensor)

        url = detail_url(measurement.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_other_users_measurement_error(self):
        """Test trying to delete another users measurement gives error."""
        new_user = create_user(email="user2@example.com",
                               password="sdklfjölohj")
        sensor = create_sensor(user=new_user)
        measurement = create_measurement(user=new_user, sensor=sensor)

        url = detail_url(measurement.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Measurement.objects.filter(id=measurement.id).exists())

    def test_filter_by_sensors(self):
        """Test filtering measurements by sensors."""
        s1 = create_sensor(user=self.user)
        s2 = create_sensor(user=self.user)
        s3 = create_sensor(user=self.user)
        m1 = create_measurement(user=self.user, sensor=s1)
        m2 = create_measurement(user=self.user, sensor=s2)
        m3 = create_measurement(user=self.user, sensor=s3)

        params = {"sensors": f"{s1.id},{s2.id}"}
        res = self.client.get(MEASUREMENTS_URL, params)

        sm1 = MeasurementSerializer(m1)
        sm2 = MeasurementSerializer(m2)
        sm3 = MeasurementSerializer(m3)
        self.assertIn(sm1.data, res.data)
        self.assertIn(sm2.data, res.data)
        self.assertNotIn(sm3.data, res.data)

    def test_filter_by_start_date(self):
        measurements = create_measurements(user=self.user)
        date = measurements[-1].timestamp
        start_date = date - timedelta(days=5)

        params = {"start_date": start_date.strftime("%Y-%m-%d")}
        res = self.client.get(MEASUREMENTS_URL, params)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        for measurement in measurements:
            if measurement.timestamp < start_date:
                self.assertNotIn(MeasurementSerializer(
                    measurement).data, res.data)
            else:
                self.assertIn(MeasurementSerializer(
                    measurement).data, res.data)

    def test_filter_by_end_date(self):
        measurements = create_measurements(user=self.user)
        date = measurements[-1].timestamp

        end_date = date - timedelta(days=5)

        params = {"end_date": end_date.strftime("%Y-%m-%d")}
        res = self.client.get(MEASUREMENTS_URL, params)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        for measurement in measurements:
            if measurement.timestamp < end_date:
                self.assertIn(MeasurementSerializer(
                    measurement).data, res.data)
            else:
                self.assertNotIn(MeasurementSerializer(
                    measurement).data, res.data)

    def test_filter_by_date(self):
        measurements = create_measurements(user=self.user)
        date = measurements[-1].timestamp

        start_date = date - timedelta(days=3)
        end_date = date - timedelta(days=6)

        params = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d")
        }
        res = self.client.get(MEASUREMENTS_URL, params)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        for measurement in measurements:
            if measurement.timestamp < start_date:
                self.assertNotIn(MeasurementSerializer(
                    measurement).data, res.data)
            elif measurement.timestamp < end_date:
                self.assertIn(MeasurementSerializer(
                    measurement).data, res.data)
            else:
                self.assertNotIn(MeasurementSerializer(
                    measurement).data, res.data)
