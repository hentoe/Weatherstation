"""
Django admin customizaiton.
"""
import os

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from core import models
from core.models import Measurement


class UserAdmin(BaseUserAdmin):
    """Define the admin pages for users."""
    ordering = ["id"]
    list_display = ["email", "name"]
    fieldsets = (
        (None, {"fields": ("email", "password", "name")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                )
            }
        ),
        (_("Important dates"), {"fields": ("last_login",)}),
    )
    readonly_fields = ["last_login"]
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "password1",
                "password2",
                "name",
                "is_active",
                "is_staff",
                "is_superuser",
            )
        }),
    )

@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    """
    Admin view for Measurement model
    """

    list_display = ["timestamp", "value", "sensor", "user"]
    readonly_fields = ["timestamp"]


admin.site.register(models.User, UserAdmin)
admin.site.register(models.Sensor)
admin.site.register(models.Location)
admin.site.register(models.SensorType)
admin.site.site_url = os.environ.get("VUE_FRONTEND_DOMAIN", "/")
