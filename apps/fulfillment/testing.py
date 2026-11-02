"""Builders for fulfillment tests and the browser tests' sample data: the
demo catalog (with stock), boxes, a sealed scale and paid orders."""

import tempfile
from datetime import date, timedelta
from decimal import Decimal

from django.utils import timezone

from apps.catalog.models import SizeOption
from apps.checkout.models import Order, OrderLine
from apps.inventory.models import Item, Lot, Supplier
from apps.storefront import demo

from .models import BoxSize, Scale

PACKER = "Teashop LLC\n1 Main St\nAlbany, NY 12207"
# Settings for fulfillment tests: the stand-in carriers and payments,
# emails kept in memory, label files in a scratch folder.
TEST_SETTINGS = dict(
    PAYMENT_PROVIDER="fake", SHIPPING_PROVIDER="fake", LABEL_PACKER_ADDRESS=PACKER,
    OWNER_NOTIFY_EMAIL="owner@example.com", EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    PRIVATE_MEDIA_ROOT=tempfile.mkdtemp(prefix="teashop-fulfillment-tests-"), SHIPPING_LABEL_FORMAT="PDF",
    PACKAGE_LABEL_SIZE="4x2", STOREFRONT_OPEN=True,
)


def shop():
    """The demo catalog with stock, two boxes with filler, and a scale."""
    # The allergens a migration made, in case the database was emptied
    # since (browser tests flush it between tests).
    import importlib

    from django.apps import apps

    importlib.import_module("apps.inventory.migrations.0002_major_allergens").add_allergens(apps, None)
    demo.load()
    supplier = Supplier.objects.get_or_create(name="Box Supplier")[0]

    def stock(code, name, kind, quantity):
        item = Item.objects.get_or_create(code=code, defaults={"name": name, "kind": kind})[0]
        if not item.lots.exists():
            Lot.objects.create(item=item, quantity_received=quantity, supplier=supplier)
        return item

    filler = stock("PAPER", "Crinkle paper (handful)", Item.Kind.PACKAGING, 200)
    small = stock("BOX-S", "Small box", Item.Kind.SHIPPING_BOX, 30)
    large = stock("BOX-L", "Large box", Item.Kind.SHIPPING_BOX, 10)
    BoxSize.objects.get_or_create(item=small, defaults=dict(
        length_in=Decimal("7"), width_in=Decimal("5"), height_in=Decimal("5"), empty_grams=90, filler=filler,
        filler_quantity=1))
    BoxSize.objects.get_or_create(item=large, defaults=dict(
        length_in=Decimal("12"), width_in=Decimal("9"), height_in=Decimal("6"), empty_grams=220, filler=filler,
        filler_quantity=2))
    scale = Scale.objects.get_or_create(serial_number="SN-4471", defaults=dict(
        name="Bench scale", make_model="Ohaus Ranger 3000", ntep_certificate="13-123", registration="ALB-0042",
        sealed_on=date.today() - timedelta(days=60), inspection_due=date.today() + timedelta(days=300)))[0]
    return scale


def size(slug, net=None):
    sizes = SizeOption.objects.filter(product__slug=slug)
    if net:
        sizes = sizes.filter(net_grams=net)
    return sizes.order_by("net_grams").first()


def paid_order(lines, *, email="ada@example.com", name="Ada Lovelace", ship_by=None, service="USPS Ground Advantage"):
    """A paid order for [(size_option, quantity)] (stand-in payment)."""
    subtotal = sum((s.price * q for s, q in lines), Decimal("0.00"))
    shipping = Decimal("5.40")
    order = Order(email=email, status=Order.Status.PAID, subtotal=subtotal, shipping_service=service,
                  shipping_amount=shipping, shipping_cost=shipping, total=subtotal + shipping,
                  amount_received=subtotal + shipping, payment_provider="fake", paid_at=timezone.now(),
                  ship_by=ship_by or (date.today() + timedelta(days=3)), address_verified=True,
                  ship_name=name, ship_street1="12 Main St", ship_city="Albany", ship_state="NY", ship_zip="12207")
    order.save()
    order.payment_id = f"fake_pi_{order.number}"
    order.save(update_fields=["payment_id"])
    for s, quantity in lines:
        OrderLine.objects.create(order=order, size_option=s, kind=OrderLine.Kind.TEA if s.net_grams else
                                 OrderLine.Kind.GOODS, product_name=s.product.name, size_name=s.name, sku=s.sku,
                                 unit_price=s.price, quantity=quantity, line_total=s.price * quantity,
                                 taxable=not s.net_grams)
    return order
