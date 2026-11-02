from django.urls import path

from . import views

app_name = "emaillist"

urlpatterns = [
    path("email-list/", views.sign_up, name="sign_up"),
    path("email-list/confirm/<str:token>/", views.confirm, name="confirm"),
    path("email-list/manage/<str:token>/", views.manage, name="manage"),
    path("email-list/unsubscribe/<str:token>/", views.unsubscribe, name="unsubscribe"),
    path("owner/email-list/", views.owner_home, name="owner_home"),
    path("owner/email-list/new/", views.mailing_edit, name="mailing_new"),
    path("owner/email-list/<int:pk>/", views.mailing, name="mailing"),
    path("owner/email-list/<int:pk>/edit/", views.mailing_edit, name="mailing_edit"),
    path("owner/email-list/<int:pk>/approve/", views.mailing_approve, name="mailing_approve"),
    path("owner/email-list/<int:pk>/withdraw/", views.mailing_withdraw, name="mailing_withdraw"),
]
