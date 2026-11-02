from django.urls import path

from . import views

app_name = "purchasing"

urlpatterns = [
    path("reorder/", views.reorder, name="reorder"),
    path("losses/", views.losses, name="losses"),
    path("profit/", views.profit, name="profit"),
]
