"""
URL mappings for the user API.
"""

from django.urls import re_path

from knox import views as knox_views

from user import views

app_name = "user"

urlpatterns = [
    re_path(r"login/", views.LoginView.as_view(), name="knox_login"),
    re_path(r"token/", views.CreateTokenView.as_view(), name="token"),
    re_path(r"logout/", knox_views.LogoutView.as_view(), name="knox_logout"),
    re_path(
        r"logoutall/",
        knox_views.LogoutAllView.as_view(),
        name="knox_logoutall",
    ),
]
