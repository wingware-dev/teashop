from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path("files/<path:name>", views.private_file, name="private_file"),
    path("lots/<int:pk>/trace/", views.lot_trace, name="lot_trace"),
]
