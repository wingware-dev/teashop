from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from two_factor.admin import AdminSiteOTPRequired
from two_factor.urls import urlpatterns as two_factor_urlpatterns

# The admin is only reachable after a two-factor login; its own login page
# redirects to the two-factor one.
admin.site.__class__ = AdminSiteOTPRequired
admin.site.site_header = "Teashop back office"
admin.site.site_title = "Teashop back office"

urlpatterns = [
    path("", include(two_factor_urlpatterns)),
    path(settings.ADMIN_URL, admin.site.urls),
    path("", include("apps.core.urls")),
]
