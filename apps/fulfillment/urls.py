from django.urls import path

from . import views

app_name = "fulfillment"

OWNER = "owner/fulfillment/"

urlpatterns = [
    path(OWNER, views.queue, name="queue"),
    path(f"{OWNER}packing-list/", views.packing_list, name="packing_list"),
    path(f"{OWNER}pickups/", views.pickups, name="pickups"),
    path(f"{OWNER}pickups/<int:pk>/", views.pickup_action, name="pickup_action"),
    path(f"{OWNER}orders/<str:number>/", views.order_detail, name="order"),
    path(f"{OWNER}orders/<str:number>/address/", views.change_address, name="address"),
    path(f"{OWNER}orders/<str:number>/refund/", views.refund, name="refund"),
    path(f"{OWNER}orders/<str:number>/cancel/", views.cancel, name="cancel"),
    path(f"{OWNER}orders/<str:number>/reship/", views.reship, name="reship"),
    path(f"{OWNER}orders/<str:number>/delay/", views.delay_notice, name="delay_notice"),
    path(f"{OWNER}parcels/<int:parcel_pk>/pack/<int:line_pk>/", views.pack, name="pack"),
    path(f"{OWNER}parcels/<int:parcel_pk>/package-labels.pdf", views.package_labels, name="package_labels"),
    path(f"{OWNER}parcels/<int:parcel_pk>/label/", views.buy_label, name="buy_label"),
    path(f"{OWNER}parcels/<int:parcel_pk>/backorder/", views.backorder, name="backorder"),
    path(f"{OWNER}packages/<int:pk>/unpack/", views.unpack, name="unpack"),
    path(f"{OWNER}labels/<int:pk>/", views.shipping_label, name="shipping_label"),
    path(f"{OWNER}labels/<int:pk>/void/", views.void_label, name="void_label"),
    # The installable web app: its manifest and service worker sit inside
    # the app's scope, and hold nothing private (no sign-in needed).
    path(f"{OWNER}manifest.webmanifest", views.manifest, name="manifest"),
    path(f"{OWNER}sw.js", views.service_worker, name="service_worker"),
    path(f"{OWNER}offline/", views.offline, name="offline"),
    # The customer's answer to a delay notice (the secret in the order link).
    path("orders/<str:token>/delay/<int:pk>/", views.delay_answer, name="delay_answer"),
]
