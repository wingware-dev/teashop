from django.urls import path

from . import views

app_name = "marketing"

# Under owner/marketing/ (config/urls.py).
urlpatterns = [
    path("", views.home, name="home"),
    path("suggest/", views.suggest, name="suggest"),
    path("ideas/<int:pk>/", views.idea, name="idea"),
    path("ideas/<int:pk>/draft/", views.idea_draft, name="idea_draft"),
    path("posts/new/", views.post_new, name="post_new"),
    path("posts/<int:pk>/", views.post, name="post"),
    path("calendar/", views.calendar, name="calendar"),
    path("campaigns/", views.campaigns, name="campaigns"),
    path("campaigns/<int:pk>/", views.campaign, name="campaign"),
    path("articles/<int:pk>/", views.article, name="article"),
]
