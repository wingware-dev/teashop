from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("healthz", views.healthz, name="healthz"),
    path("owner/", views.owner_dashboard, name="owner_dashboard"),
    path("account/logout/", LogoutView.as_view(), name="logout"),
]
