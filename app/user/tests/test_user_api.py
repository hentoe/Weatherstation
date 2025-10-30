"""
Tests for the user API.
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse("user-list")
LOGIN_URL = reverse("user:knox_login")
TOKEN_URL = reverse("user:token")
ME_URL = "/api/users/me/"

User = get_user_model()


def create_user(**params):
    """Create and return a new user."""
    return User.objects.create_user(**params)


@pytest.fixture
def api_client():
    """Fixture to create an API client for testing."""
    return APIClient()


@pytest.mark.django_db
class TestPublicUserApi:
    """Test the public features of the user API."""

    @pytest.fixture(autouse=True)
    def setup_client(self):
        """Fixture to create an API client for testing."""
        self.client = APIClient()

    def test_create_user_success(self):
        """Test creating a user is successful."""
        payload = {
            "email": "test@example.com",
            "password": "supersecurepassword123",
            "re_password": "supersecurepassword123",
            "name": "Test Name",
        }
        response = self.client.post(CREATE_USER_URL, payload)

        assert response.status_code == status.HTTP_201_CREATED

        user = User.objects.get(email=payload["email"])
        assert user.check_password(payload["password"]) is True
        assert "password" not in response.data
        assert user.name == payload["name"]

    def test_create_user_with_email_exists_error(self):
        """Test error returned if user with email exists."""
        payload = {
            "email": "test@example.com",
            "password": "supersecurepassword123",
            "name": "Test Name",
        }
        create_user(**payload)
        payload["re_password"] = payload["password"]
        response = self.client.post(CREATE_USER_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_too_short_error(self):
        """Test an error is returned if password less than 5 chars."""
        payload = {
            "email": "test@example.com",
            "password": "test",
            "re_password": "test",
            "name": "Test Name",
        }
        response = self.client.post(CREATE_USER_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        user_exists = (
            get_user_model().objects.filter(email=payload["email"]).exists()
        )
        assert not user_exists

    def test_create_token_for_user(self):
        """Test generates token for valid credentials."""
        user_details = {
            "name": "Test Name",
            "email": "test@example.com",
            "password": "test-user-password1234ztghads",
        }
        create_user(**user_details)

        payload = {
            "email": user_details["email"],
            "password": user_details["password"],
        }
        response = self.client.post(TOKEN_URL, payload)

        assert "expiry" not in response.data
        assert response.status_code == status.HTTP_200_OK

    def test_create_knox_token_for_user(self):
        """Test generates knox token for valid credentials."""
        user_details = {
            "name": "Test Name",
            "email": "test@example.com",
            "password": "test-user-password1234ztghads",
        }
        create_user(**user_details)

        payload = {
            "email": user_details["email"],
            "password": user_details["password"],
        }
        response = self.client.post(LOGIN_URL, payload)

        assert "token" in response.data
        assert "expiry" in response.data
        assert response.status_code == status.HTTP_200_OK

    def test_create_token_bad_credentials(self):
        """Test returns error if credentials are invalid"""
        create_user(email="test@example.com", password="goodpassword")

        payload = {"email": "test@example.com", "password": "badpass"}
        response = self.client.post(LOGIN_URL, payload)

        assert "token" not in response.data
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_token_blank_password(self):
        """Test posting a blank password returns an error."""
        create_user(email="test@example.com", password="goodpassword")

        payload = {"email": "test@example.com", "password": ""}
        response = self.client.post(LOGIN_URL, payload)

        assert "token" not in response.data
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_retrieve_user_unauthorized(self):
        """Test authentication is required for users."""
        response = self.client.get(ME_URL)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication."""

    def setUp(self):
        self.user = create_user(
            email="test@example.com",
            password="supersecurepassword123",
            name="Test Name",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user."""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            res.data,
            {
                "name": self.user.name,
                "email": self.user.email,
                "is_staff": self.user.is_staff
            },
        )

    def test_post_me_not_allowed(self):
        """Test POST is not allowed for the me endpoint."""
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the user profile for the authenticated user."""
        payload = {"name": "Updated name"}

        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload["name"])
        self.assertEqual(res.status_code, status.HTTP_200_OK)
