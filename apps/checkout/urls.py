from django.urls import path

from . import account_views, owner_views, subscription_views, views, webhooks

app_name = "checkout"

urlpatterns = [
    path("cart/", views.cart_page, name="cart"),
    path("cart/add/", views.cart_add, name="cart_add"),
    path("cart/update/", views.cart_update, name="cart_update"),
    path("cart/discount/", views.cart_discount, name="cart_discount"),
    path("checkout/", views.address_step, name="address"),
    path("checkout/shipping/", views.shipping_step, name="shipping"),
    path("checkout/pay/", views.pay_step, name="pay"),
    path("checkout/pay/test/", views.fake_pay, name="fake_pay"),
    path("checkout/complete/", views.complete, name="complete"),
    path("checkout/stripe-webhook/", webhooks.stripe_webhook, name="stripe_webhook"),
    path("orders/<str:token>/", views.order_status, name="order_status"),
    path("subscriptions/", subscription_views.plans, name="plans"),
    path("subscriptions/join/<slug:slug>/", subscription_views.subscribe, name="subscribe"),
    path("subscriptions/pay/<str:token>/", subscription_views.pay, name="subscription_pay"),
    path("subscriptions/pay/<str:token>/test/", subscription_views.fake_pay, name="subscription_fake_pay"),
    path("subscriptions/welcome/<str:token>/", subscription_views.welcome, name="subscription_welcome"),
    path("subscriptions/cancel/<str:token>/", subscription_views.cancel, name="subscription_cancel"),
    path("your-account/", account_views.account, name="account"),
    path("your-account/sign-in/", account_views.sign_in, name="sign_in"),
    path("your-account/sign-in/<str:token>/", account_views.sign_in_link, name="sign_in_link"),
    path("your-account/sign-out/", account_views.sign_out, name="sign_out"),
    path("your-account/orders/<str:number>/buy-again/", account_views.buy_again, name="buy_again"),
    path("owner/checkout/sales-by-state/", owner_views.sales_by_state, name="sales_by_state"),
]
