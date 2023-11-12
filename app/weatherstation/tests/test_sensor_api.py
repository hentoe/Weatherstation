"""
Tests for sensor APIs.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Location,
    Sensor,
    SensorType
)

from weatherstation.serializers import (
    SensorSerializer,
    SensorDetailSerializer,
)
from weatherstation.tests.test_location_api import create_location
from weatherstation.tests.test_sensor_type_api import create_sensor_type

SENSORS_URL = reverse("weatherstation:sensor-list")


def detail_url(sensor_id):
    """Create and return a sensor detail URL."""
    return reverse("weatherstation:sensor-detail", args=[sensor_id])


def create_sensor(user, **params):
    """Create and return a sample sensor"""
    defaults = {
        "name": "Sample sensor name",
        "description": "Sample description",
    }
    defaults.update(params)

    sensor = Sensor.objects.create(user=user, **defaults)

    return sensor


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicSensorAPITests(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(SENSORS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateSensorAPITests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email="user@example.com", password="testp1235")
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
        other_user = create_user(
            email="other@example.com", password="password1234")
        create_sensor(user=other_user)
        create_sensor(user=self.user)

        res = self.client.get(SENSORS_URL)

        sensors = Sensor.objects.filter(user=self.user)
        serializer = SensorSerializer(sensors, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_sensor_detail(self):
        """Test get sensor detail."""
        sensor = create_sensor(user=self.user)

        url = detail_url(sensor.id)
        res = self.client.get(url)

        serializer = SensorDetailSerializer(sensor)
        self.assertEqual(res.data, serializer.data)

    def test_create_sensor(self):
        """Test creating a sensor."""
        payload = {
            "name": "Test sensor",
            "description": "Sample description",
        }
        res = self.client.post(SENSORS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        sensor = Sensor.objects.get(id=res.data["id"])
        for k, v in payload.items():
            self.assertEqual(getattr(sensor, k), v)
        self.assertEqual(sensor.user, self.user)

    def test_partial_update(self):
        """Test partial update of a sensor."""
        original_description = "This is the original description"
        sensor = create_sensor(
            user=self.user,
            name="Test Sensor",
            description=original_description,
        )

        payload = {"name": "Temperature Sensor"}
        url = detail_url(sensor.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        sensor.refresh_from_db()
        self.assertEqual(sensor.name, payload["name"])
        self.assertEqual(sensor.description, original_description)
        self.assertEqual(sensor.user, self.user)

    def test_full_update(self):
        """Test full update of sensor."""
        sensor = create_sensor(
            user=self.user,
            name="Test Sensor",
            description="Description",
        )

        payload = {
            "name": "Temperature Sensor",
            "description": "New Description"
        }

        url = detail_url(sensor.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        sensor.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(sensor, k), v)
        self.assertEqual(sensor.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the sensor user results in an error."""
        new_user = create_user(email="user2@example.com",
                               password="sdklfjölohj")
        sensor = create_sensor(user=self.user)

        payload = {"user": new_user.id}
        url = detail_url(sensor.id)
        self.client.patch(url, payload)

        sensor.refresh_from_db()
        self.assertEqual(sensor.user, self.user)

    def test_delete_sensor(self):
        """Test deleting a sensor successful."""
        sensor = create_sensor(user=self.user)

        url = detail_url(sensor.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_other_users_sensor_error(self):
        """Test trying to delete another users sensor gives error."""
        new_user = create_user(email="user2@example.com",
                               password="alsdkfnalkösdfhj")
        sensor = create_sensor(user=new_user)

        url = detail_url(sensor.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Sensor.objects.filter(id=sensor.id).exists())

    def test_create_sensor_with_new_type(self):
        """Test creating a sensor with a new sensor type."""
        payload = {
            "name": "BME280",
            "description": "Sample description",
            "sensor_type": {"name": "Temperature", "unit": "°C"},
        }
        res = self.client.post(SENSORS_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        sensors = Sensor.objects.filter(user=self.user)
        sensor = sensors[0]
        self.assertEqual(sensor.sensor_type.name,
                         payload["sensor_type"]["name"])

    def test_create_sensor_with_existing_type(self):
        """Test creating a sensor with existing sensor type."""
        sensor_type = SensorType.objects.create(
            user=self.user,
            name="Temperature",
            unit="°C"
        )
        payload = {
            "name": "BME280",
            "description": "Sample description",
            "sensor_type": {"name": "Temperature", "unit": "°C"}
        }
        res = self.client.post(SENSORS_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        sensors = Sensor.objects.filter(user=self.user)
        self.assertEqual(sensors.count(), 1)
        sensor = sensors[0]
        self.assertEqual(sensor_type, sensor.sensor_type)

    def test_create_sensor_with_new_location(self):
        """Test creating a sensor with a new location."""
        payload = {
            "name": "BME280",
            "description": "Sample description",
            "location": {"name": "Garden"},
        }
        res = self.client.post(SENSORS_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        sensors = Sensor.objects.filter(user=self.user)
        sensor = sensors[0]
        self.assertEqual(sensor.location.name,
                         payload["location"]["name"])

    def test_create_sensor_with_existing_location(self):
        """Test creating a sensor with existing location."""
        location = Location.objects.create(
            user=self.user,
            name="Garage"
        )
        payload = {
            "name": "BME280",
            "description": "Sample description",
            "location": {"name": "Garage"},
        }
        res = self.client.post(SENSORS_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        sensors = Sensor.objects.filter(user=self.user)
        self.assertEqual(sensors.count(), 1)
        sensor = sensors[0]
        self.assertEqual(location, sensor.location)

    def test_update_sensor_with_existing_type(self):
        """Test updating a sensor with existing sensor type."""
        sensor_type = SensorType.objects.create(
            user=self.user,
            name="Temperature",
            unit="°C"
        )
        sensor = create_sensor(user=self.user)
        payload = {
            "sensor_type": {"name": "Temperature", "unit": "°C"}
        }
        url = detail_url(sensor.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        sensor.refresh_from_db()
        self.assertEqual(sensor_type, sensor.sensor_type)

    def test_update_sensor_with_existing_location(self):
        """Test updating a sensor with existing location."""
        location = Location.objects.create(
            user=self.user,
            name="Garage"
        )
        sensor = create_sensor(user=self.user)
        payload = {
            "location": {"name": "Garage"},
        }
        url = detail_url(sensor.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        sensor.refresh_from_db()
        self.assertEqual(location, sensor.location)

    def test_filter_by_sensor_types(self):
        """Test filtering sensors by sensor types."""
        st1 = create_sensor_type(user=self.user)
        st2 = create_sensor_type(user=self.user)
        st3 = create_sensor_type(user=self.user)
        s1 = create_sensor(user=self.user, sensor_type=st1)
        s2 = create_sensor(user=self.user, sensor_type=st2)
        s3 = create_sensor(user=self.user, sensor_type=st3)

        params = {"sensor_types": f"{st1.id},{st2.id}"}
        res = self.client.get(SENSORS_URL, params)

        ss1 = SensorSerializer(s1)
        ss2 = SensorSerializer(s2)
        ss3 = SensorSerializer(s3)
        self.assertIn(ss1.data, res.data)
        self.assertIn(ss2.data, res.data)
        self.assertNotIn(ss3.data, res.data)

    def test_filter_by_locations(self):
        """Test filtering sensors by locations."""
        l1 = create_location(user=self.user)
        l2 = create_location(user=self.user)
        l3 = create_location(user=self.user)
        s1 = create_sensor(user=self.user, location=l1)
        s2 = create_sensor(user=self.user, location=l2)
        s3 = create_sensor(user=self.user, location=l3)

        params = {"locations": f"{l1.id},{l2.id}"}
        res = self.client.get(SENSORS_URL, params)

        ss1 = SensorSerializer(s1)
        ss2 = SensorSerializer(s2)
        ss3 = SensorSerializer(s3)
        self.assertIn(ss1.data, res.data)
        self.assertIn(ss2.data, res.data)
        self.assertNotIn(ss3.data, res.data)
