from django.urls import path

from . import views

app_name = "support"

urlpatterns = [
    path("help/chat/", views.chat_start, name="chat_start"),
    path("help/chat/<str:token>/", views.chat, name="chat"),
    path("help/chat/<str:token>/messages/", views.chat_messages, name="chat_messages"),
    path("owner/support/", views.owner_inbox, name="owner_inbox"),
    path("owner/support/<int:pk>/", views.owner_conversation, name="owner_conversation"),
    path("owner/support/<int:pk>/discard-draft/", views.owner_discard_draft, name="owner_discard_draft"),
    path("owner/support/<int:pk>/close/", views.owner_close, name="owner_close"),
    path("owner/support/categories/<str:category>/", views.owner_category, name="owner_category"),
]
