"""
Database models.
"""

from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Manager for users."""

    def create_user(self, email, password=None, **extra_fields):
        """Create, save and return a new user."""
        if not email:
            raise ValueError(_("User must have an email address."))
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        """Create and return a new superuser."""
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """User in the system."""

    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"


class Location(models.Model):
    """Location object."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    @cached_property
    def is_assigned(self):
        return self.sensor_set.exists()

    class Meta:
        ordering = ['name']
        verbose_name = _("Location")
        verbose_name_plural = _("Locations")


class SensorType(models.Model):
    """Sensor Type object."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    unit = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name

    @cached_property
    def is_assigned(self):
        return self.sensor_set.exists()

    class Meta:
        ordering = ['name']
        verbose_name = _("Sensor Type")
        verbose_name_plural = _("Sensor Types")


class Sensor(models.Model):
    """Sensor object."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sensor_type = models.ForeignKey(
        SensorType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sensors"
    )
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sensors"
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = _("Sensor")
        verbose_name_plural = _("Sensors")


class Measurement(models.Model):
    """Measurement object."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    value = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    sensor = models.ForeignKey(Sensor,
                               on_delete=models.CASCADE,
                               related_name="measurements")

    def __str__(self):
        return f"{self.sensor} - {self.timestamp} - {self.value}"

    class Meta:
        ordering = ['timestamp']
        verbose_name = _("Measurement")
        verbose_name_plural = _("Measurements")
