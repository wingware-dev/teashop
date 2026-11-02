from django.urls import path

from . import views

app_name = "ops"

urlpatterns = [
    path("", views.owner_home, name="owner_home"),
    path("check/", views.check_now, name="check_now"),
    path("proposals/<int:pk>/", views.decide, name="decide"),
    path("review/", views.review_page, name="review"),
]
