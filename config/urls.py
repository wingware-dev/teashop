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
    path("owner/inventory/", include("apps.inventory.urls")),
    path("owner/purchasing/", include("apps.purchasing.urls")),
    path("", include("apps.core.urls")),
    # Packing and shipping (owner/fulfillment/...), and customers' answers
    # to delay notices.
    path("", include("apps.fulfillment.urls")),
    # Cart, checkout, orders, subscriptions and customer accounts.
    path("", include("apps.checkout.urls")),
    # The shop: the home page, catalog pages, robots.txt and sitemap.xml.
    path("", include("apps.storefront.urls")),
]

# On a laptop (DEBUG) Django serves uploaded product photos itself; on the
# server Caddy serves them (deploy/caddy/Caddyfile).
if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
