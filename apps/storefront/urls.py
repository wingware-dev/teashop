from django.contrib.sitemaps.views import sitemap
from django.urls import path

from apps.catalog.models import Category

from . import owner_views, views
from .sitemaps import SITEMAPS

app_name = "storefront"

urlpatterns = [
    path("", views.home, name="home"),
    path("teas/", views.all_teas, name="all_teas"),
    path("teas/<slug:slug>/", views.category, {"section": Category.Section.TEA}, name="category"),
    path("merch-and-accessories/", views.goods, name="goods"),
    path("merch-and-accessories/<slug:slug>/", views.category, {"section": Category.Section.GOODS},
         name="goods_category"),
    path("regions/", views.region_list, name="regions"),
    path("regions/<slug:slug>/", views.region, name="region"),
    path("collections/<slug:slug>/", views.collection, name="collection"),
    path("products/<slug:slug>/", views.product, name="product"),
    path("search/", views.search, name="search"),
    path("tea-notes/", views.article_list, name="articles"),
    path("tea-notes/<slug:slug>/", views.article, name="article"),
    path("policies/<slug:slug>/", views.policy, name="policy"),
    path("robots.txt", views.robots_txt, name="robots"),
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
    path("owner/page-designs/", owner_views.variant_list, name="variant_list"),
    path("owner/page-designs/<int:pk>/", owner_views.variant_preview, name="variant_preview"),
    path("owner/page-designs/<int:pk>/decide/", owner_views.variant_decide, name="variant_decide"),
]
