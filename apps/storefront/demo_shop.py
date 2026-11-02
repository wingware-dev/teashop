"""Sample day-to-day business for a development database, on top of the
demo catalog (demo.py): suppliers and deliveries, packaging and shipping
supplies, box sizes, package dimensions and a scale, orders at each stage, a subscription,
email-list subscribers with a draft mailing, a support conversation and
marketing ideas.

Load it with ``python manage.py load_demo_shop`` (refused unless DEBUG
is on).  Safe to run again: each record is looked up by a fixed name,
code or example.com email first and only made if missing.  Everything
here is invented; the emails are at example.com, which never delivers.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.catalog.models import Product, SizeOption
from apps.checkout.models import Customer, Order, OrderLine, Subscription, SubscriptionPlan
from apps.emaillist.models import ConsentEvent, Mailing, Subscriber
from apps.fulfillment.models import BoxSize, PackageDimensions, Scale
from apps.inventory.models import Item, Lot, Receipt, Supplier
from apps.marketing.models import Campaign, Idea
from apps.support.models import Conversation, Draft, Message

from . import demo

SUPPLIERS = [
    dict(name="Demo Tea Importers", contact_name="Priya Raman", email="orders@demo-tea-importers.example.com",
         phone="555-0100", lead_time_days=21, notes="Bulk Indian and Chinese teas; minimum order 5 kg."),
    dict(name="Highland Leaf Co. (demo)", contact_name="Kenji Mori", email="sales@highland-leaf.example.com",
         phone="555-0101", lead_time_days=35, notes="Japanese and Taiwanese teas, shipped by air."),
    dict(name="Northside Packaging (demo)", contact_name="Dana Kowalski", email="hello@northside-pack.example.com",
         phone="555-0102", lead_time_days=7, notes="Pouches, tins, labels, boxes and mailers."),
]

# Second deliveries of some teas, from the second supplier: code, grams,
# days ago, landed cost per kg, harvest year.
REORDERS = [
    ("SENCHA-MORNING-MIST", 2000, 18, "62.00", 2026),
    ("DONG-DING-OOLONG", 1500, 18, "88.00", 2026),
]

# code, name, pieces, landed cost each
SUPPLIES = [
    ("TISSUE", "Tissue paper sheet (filler)", 400, "0.05"),
    ("MAILER-6X9", "Padded mailer 6 × 9 in", 150, "0.42"),
    ("BOX-8X6X4", "Shipping box 8 × 6 × 4 in", 80, "0.85"),
    ("BOX-12X9X6", "Shipping box 12 × 9 × 6 in", 40, "1.40"),
]

# item code, length, width, height, empty grams, most grams, filler pieces
BOXES = [
    ("MAILER-6X9", "9", "6", "1.5", 25, 450, 0),
    ("BOX-8X6X4", "8", "6", "4", 120, 2500, 2),
    ("BOX-12X9X6", "12", "9", "6", 260, 9000, 4),
]

# Outside size of one packed package of the demo teas' sizes, for the
# box suggestion: (package, net grams) -> (length, width, height) in inches.
PACKAGE_DIMENSIONS = {
    ("pouch", 25): ("5", "3.5", "1.25"),
    ("pouch", 30): ("5", "3.5", "1.5"),
    ("pouch", 50): ("6", "4", "1.5"),
    ("tin", 25): ("2.75", "2.75", "3"),
    ("tin", 50): ("3", "3", "4"),
    ("tin", 100): ("3.25", "3.25", "5.5"),
}

CUSTOMERS = [
    dict(email="maya.okafor@example.com", ship_name="Maya Okafor", ship_street1="14 Elm Street",
         ship_city="Ithaca", ship_state="NY", ship_zip="14850"),
    dict(email="leo.hartmann@example.com", ship_name="Leo Hartmann", ship_street1="220 Oak Avenue Apt 3",
         ship_city="Portland", ship_state="OR", ship_zip="97205"),
    dict(email="ana.silva@example.com", ship_name="Ana Silva", ship_street1="9 Harbor Road",
         ship_city="Salem", ship_state="MA", ship_zip="01970"),
    dict(email="sam.whitfield@example.com", ship_name="Sam Whitfield", ship_street1="77 Prairie Lane",
         ship_city="Madison", ship_state="WI", ship_zip="53703"),
]

# Orders, each found again by its payment id.  lines: (sku, quantity).
ORDERS = [
    dict(key="demo_pending", customer=3, status="pending", days_ago=0,
         lines=[("DARJEELING-F-25", 1)], note="Abandoned at payment"),
    dict(key="demo_paid_due", customer=0, status="paid", days_ago=1,
         lines=[("ASSAM-SECOND-50", 2), ("SENCHA-MORNI-100", 1)]),
    dict(key="demo_paid_allergen", customer=1, status="paid", days_ago=1,
         lines=[("VANILLA-ALMO-50", 1), ("CHAMOMILE-ME-30", 1), ("GLASS-TEAPOT", 1)]),
    dict(key="demo_paid_late", customer=2, status="paid", days_ago=4,
         lines=[("SILVER-NEEDL-25", 1)]),
    dict(key="demo_shipped", customer=0, status="shipped", days_ago=6,
         lines=[("EARL-GREY-CO-100", 1), ("YUNNAN-GOLDE-50", 1)]),
    dict(key="demo_cancelled", customer=3, status="cancelled", days_ago=9,
         lines=[("HIBISCUS-BER-50", 2)]),
]

PLAN = dict(slug="monthly-discovery", name="Monthly Discovery Box",
            description="Two 50 g pouches of teas we pick each month, with brewing notes.", price=Decimal("24.00"),
            interval_months=1)

SUBSCRIBERS = [
    # email, status, frequency, days since they joined
    ("maya.okafor@example.com", Subscriber.Status.SUBSCRIBED, Subscriber.Frequency.MONTHLY, 60),
    ("leo.hartmann@example.com", Subscriber.Status.SUBSCRIBED, Subscriber.Frequency.FORTNIGHTLY, 30),
    ("jordan.lee@example.com", Subscriber.Status.SUBSCRIBED, Subscriber.Frequency.WEEKLY, 12),
    ("pat.nguyen@example.com", Subscriber.Status.PENDING, Subscriber.Frequency.MONTHLY, 1),
    ("chris.baker@example.com", Subscriber.Status.UNSUBSCRIBED, Subscriber.Frequency.MONTHLY, 90),
]

MAILING = dict(
    subject="New this month: first flush Darjeeling and golden Yunnan buds",
    body="Two new teas arrived this month.\n\n"
         "Darjeeling First Flush is the spring's first picking: light, bright and flowery.\n\n"
         "Yunnan Golden Buds are downy golden buds that brew smooth and sweet, with a note of cocoa.\n\n"
         "Both are on the shop now, in pouches and tins.",
)

IDEAS = [
    dict(title="Iced hibiscus for the last warm days", product="hibiscus-berry-tisane", made_by="owner",
         notes="Photo of the ruby-red jug on the porch; brew double strength over ice."),
    dict(title="How to brew oolong gongfu style", product="dong-ding-oolong", made_by="marketing-agent (demo)",
         notes="Short steeps, lots of leaf, many infusions: a step-by-step post with photos of each pour."),
    dict(title="Behind the scenes: weighing and sealing each pouch", product=None, made_by="owner",
         notes="Show the sealed scale and the pouch labels: why the net weight is exact."),
    dict(title="Autumn tea pairings", product="assam-second-flush", made_by="marketing-agent (demo)",
         notes="Malty Assam with apple pie, Yunnan with dark chocolate.", campaign="autumn-teas"),
]


def _suppliers():
    found = {}
    for fields in SUPPLIERS:
        supplier, _created = Supplier.objects.get_or_create(name=fields["name"], defaults=fields)
        found[fields["name"]] = supplier
    return found


def _supplies(suppliers):
    """Packaging and shipping supplies in stock, the box sizes and a scale."""
    packer = suppliers["Northside Packaging (demo)"]
    for code, name, pieces, cost in SUPPLIES:
        kind = Item.Kind.PACKAGING if code == "TISSUE" else Item.Kind.SHIPPING_BOX
        item, _created = Item.objects.get_or_create(code=code, defaults=dict(name=name, kind=kind))
        if not item.lots.exists():
            Lot.objects.create(item=item, quantity_received=pieces, supplier=packer, landed_cost=Decimal(cost),
                               received_on=timezone.localdate() - timedelta(days=30))
    Item.objects.filter(kind__in=[Item.Kind.PACKAGING, Item.Kind.SHIPPING_BOX], default_supplier=None).update(
        default_supplier=packer)
    tissue = Item.objects.get(code="TISSUE")
    for code, length, width, height, empty, most, filler in BOXES:
        BoxSize.objects.get_or_create(
            item=Item.objects.get(code=code),
            defaults=dict(length_in=Decimal(length), width_in=Decimal(width), height_in=Decimal(height),
                          empty_grams=empty, max_grams=most, filler=tissue if filler else None,
                          filler_quantity=filler))
    today = timezone.localdate()
    Scale.objects.get_or_create(
        serial_number="DEMO-0001",
        defaults=dict(name="Bench scale", make_model="Demo Scales PB-3000", ntep_certificate="00-000",
                      registration="DEMO-WM-1234", sealed_on=today - timedelta(days=120),
                      inspection_due=today + timedelta(days=245)))


def _package_dimensions():
    """Measured sizes for the demo teas' pouches and tins; sizes the owner
    made, or already measured, are left alone."""
    sizes = SizeOption.objects.filter(product__slug__in=[tea["slug"] for tea in demo.TEAS], dimensions=None)
    for size in sizes:
        measured = PACKAGE_DIMENSIONS.get((size.package, size.net_grams))
        if measured is None:
            continue
        length, width, height = (Decimal(d) for d in measured)
        PackageDimensions.objects.create(size_option=size, length_in=length, width_in=width, height_in=height)


def _deliveries(suppliers):
    """A second delivery of two teas, from the second supplier, through a
    receipt as the owner would record it."""
    highland = suppliers["Highland Leaf Co. (demo)"]
    importers = suppliers["Demo Tea Importers"]
    received_on = timezone.localdate() - timedelta(days=REORDERS[0][2])
    receipt = Receipt.objects.filter(supplier=highland, notes__startswith="Demo delivery").first()
    if receipt is None:
        receipt = Receipt.objects.create(supplier=highland, received_on=received_on,
                                         notes="Demo delivery: sencha and oolong restock")
    for code, grams, _days, cost, harvest in REORDERS:
        item = Item.objects.filter(code=code).first()
        if item is None or receipt.lots.filter(item=item).exists():
            continue
        Lot.objects.create(item=item, receipt=receipt, quantity_received=grams, harvest_year=harvest,
                           best_by=date.today() + timedelta(days=600), country_of_origin=item.lots.first()
                           .country_of_origin, landed_cost=Decimal(cost), supplier_lot_code=f"HL-{code[:6]}-26")
        item.default_supplier = item.default_supplier or highland
        item.save(update_fields=["default_supplier"])
    Item.objects.filter(kind__in=Item.BY_WEIGHT, default_supplier=None).update(default_supplier=importers)


def _customers():
    customers = []
    for fields in CUSTOMERS:
        customer, _created = Customer.objects.get_or_create(email=fields["email"], defaults=fields)
        customers.append(customer)
    return customers


def _address(customer):
    return {f: getattr(customer, f) for f in ("ship_name", "ship_street1", "ship_street2", "ship_city", "ship_state",
                                              "ship_zip")}


def _order(spec, customer, now):
    if Order.objects.filter(payment_id=spec["key"]).exists():
        return
    created = now - timedelta(days=spec["days_ago"], hours=3)
    sizes = {s.sku: s for s in SizeOption.objects.filter(sku__in=[sku for sku, _q in spec["lines"]])
             .select_related("product")}
    if len(sizes) < len(spec["lines"]):
        raise ValueError(f"Demo order {spec['key']}: a size is missing; load the demo catalog first")
    order = Order(email=customer.email, customer=customer, status=spec["status"], created_at=created,
                  payment_provider="demo", payment_id=spec["key"], shipping_service="USPS Ground Advantage",
                  shipping_cost=Decimal("5.40"), address_verified=True, **_address(customer))
    lines = []
    for sku, quantity in spec["lines"]:
        size = sizes[sku]
        goods = size.product.kind != size.product.Kind.TEA
        lines.append(OrderLine(size_option=size, kind=OrderLine.Kind.GOODS if goods else OrderLine.Kind.TEA,
                               product_name=size.product.name, size_name=size.name, sku=sku,
                               unit_price=size.price, quantity=quantity, line_total=size.price * quantity,
                               taxable=goods and customer.ship_state == "NY"))
    order.subtotal = sum(line.line_total for line in lines)
    order.shipping_amount = Decimal("0.00") if order.subtotal >= 50 else Decimal("6.00")
    order.taxable_amount = sum(line.line_total for line in lines if line.taxable)
    if order.taxable_amount:
        order.tax_rate = Decimal("0.08000")
        order.tax_jurisdiction = "Tompkins County (demo)"
        order.tax_amount = (order.taxable_amount * order.tax_rate).quantize(Decimal("0.01"))
    order.total = order.subtotal + order.shipping_amount + order.tax_amount
    if spec["status"] in (Order.Status.PAID, Order.Status.SHIPPED):
        order.paid_at = created + timedelta(minutes=2)
        order.amount_received = order.total
        order.payment_fee = (order.total * Decimal("0.029") + Decimal("0.30")).quantize(Decimal("0.01"))
        order.ship_by = order.paid_at.date() + timedelta(days=2)
        order.confirmation_sent_at = order.paid_at
    if spec["status"] == Order.Status.SHIPPED:
        order.shipped_at = created + timedelta(days=1)
        order.tracking_number = "9400100000000000000000"
        order.shipped_email_sent_at = order.shipped_at
    order.save()
    for line in lines:
        line.order = order
    OrderLine.objects.bulk_create(lines)


def _subscription(customer, now):
    plan, _created = SubscriptionPlan.objects.get_or_create(slug=PLAN["slug"], defaults=PLAN)
    if Subscription.objects.filter(plan=plan, email=customer.email).exists():
        return
    started = now - timedelta(days=40)
    subscription = Subscription.objects.create(
        plan=plan, customer=customer, email=customer.email, status=Subscription.Status.ACTIVE, price=plan.price,
        interval_months=plan.interval_months, terms_text=plan.renewal_terms(), consented_at=started,
        payment_provider="demo", current_period_end=started + timedelta(days=61), acknowledgment_sent_at=started,
        created_at=started, **_address(customer))
    # Its latest delivery, paid and waiting to be packed.
    sizes = list(SizeOption.objects.filter(sku__in=["SENCHA-MORNI-50", "DONG-DING-OO-50"]).select_related("product"))
    paid = now - timedelta(days=10)
    order = Order.objects.create(
        email=customer.email, customer=customer, subscription=subscription, status=Order.Status.PAID,
        created_at=paid, paid_at=paid, ship_by=paid.date() + timedelta(days=12), payment_provider="demo",
        payment_id="demo_subscription", subtotal=plan.price, total=plan.price, amount_received=plan.price,
        confirmation_sent_at=paid, address_verified=True, **_address(customer))
    for size in sizes:
        OrderLine.objects.create(order=order, size_option=size, kind=OrderLine.Kind.SUBSCRIPTION,
                                 product_name=size.product.name, size_name=size.name, sku=size.sku,
                                 unit_price=Decimal("0.00"), quantity=1, line_total=Decimal("0.00"))


def _email_list(now):
    for email, status, frequency, days in SUBSCRIBERS:
        if Subscriber.objects.filter(email=email).exists():
            continue
        joined = now - timedelta(days=days)
        subscriber = Subscriber.objects.create(
            email=email, status=status, frequency=frequency, requested_at=joined, confirmation_sent_at=joined,
            confirmed_at=joined + timedelta(hours=1) if status != Subscriber.Status.PENDING else None,
            unsubscribed_at=now - timedelta(days=5) if status == Subscriber.Status.UNSUBSCRIBED else None)
        events = [ConsentEvent.Action.REQUESTED]
        if subscriber.confirmed_at:
            events.append(ConsentEvent.Action.CONFIRMED)
        if subscriber.unsubscribed_at:
            events.append(ConsentEvent.Action.UNSUBSCRIBED)
        for action in events:
            ConsentEvent.objects.create(
                subscriber=subscriber, action=action, email=email, frequency=frequency,
                method=ConsentEvent.Method.FORM if action == ConsentEvent.Action.REQUESTED else ConsentEvent.Method.LINK,
                at={ConsentEvent.Action.REQUESTED: joined, ConsentEvent.Action.CONFIRMED: subscriber.confirmed_at}
                .get(action, subscriber.unsubscribed_at),
                wording="Demo sign-up (sample data)")
    Mailing.objects.get_or_create(subject=MAILING["subject"],
                                  defaults=dict(body=MAILING["body"], created_by="marketing-agent (demo)"))


def _support(now):
    subject = "Is my order on its way?"
    if Conversation.objects.filter(email="ana.silva@example.com", subject=subject).exists():
        return
    order = Order.objects.filter(payment_id="demo_paid_late").first()
    started = now - timedelta(hours=5)
    conversation = Conversation.objects.create(
        channel=Conversation.Channel.EMAIL, status=Conversation.Status.DRAFTED, category="order_status",
        email="ana.silva@example.com", name="Ana Silva", subject=subject, order=order, created_at=started,
        last_activity_at=started)
    Message.objects.create(
        conversation=conversation, sender=Message.Sender.CUSTOMER, created_at=started, handled_at=started,
        body="Hi, I ordered the Silver Needle a few days ago and haven't had a shipping email yet. "
             "Is everything all right?\n\nThanks, Ana")
    Draft.objects.create(
        conversation=conversation, category="order_status", created_at=started,
        body="Hi Ana,\n\nThank you for your patience. Your Silver Needle is being packed today and will go out "
             "with tomorrow's mail; you'll get the tracking number by email as soon as it ships.\n\n"
             "Best wishes,\nThe Teashop")
    chat_start = now - timedelta(days=2)
    chat = Conversation.objects.create(
        channel=Conversation.Channel.CHAT, status=Conversation.Status.ANSWERED, category="brewing",
        email="jordan.lee@example.com", name="Jordan", subject="Green tea tastes bitter",
        created_at=chat_start, last_activity_at=chat_start + timedelta(minutes=3))
    Message.objects.create(conversation=chat, sender=Message.Sender.CUSTOMER, created_at=chat_start,
                           handled_at=chat_start, body="My sencha always tastes bitter. What am I doing wrong?")
    Message.objects.create(
        conversation=chat, sender=Message.Sender.AGENT, created_at=chat_start + timedelta(minutes=1),
        body="Bitterness usually means the water is too hot or the steep too long. Let boiled water cool to "
             "about 75 °C and steep for one to two minutes.")


def _marketing():
    campaign, _created = Campaign.objects.get_or_create(
        slug="autumn-teas", defaults=dict(name="Autumn teas", description="Malty and roasted teas for cooler days.",
                                          starts_on=date.today() - timedelta(days=7),
                                          ends_on=date.today() + timedelta(days=45)))
    for idea in IDEAS:
        if Idea.objects.filter(title=idea["title"]).exists():
            continue
        Idea.objects.create(
            title=idea["title"], notes=idea["notes"], made_by=idea["made_by"],
            product=Product.objects.filter(slug=idea["product"]).first() if idea["product"] else None,
            campaign=campaign if idea.get("campaign") else None)


@transaction.atomic
def load(owner=None):
    """The demo catalog, then the sample business around it, skipping what
    already exists."""
    demo.load(owner)
    now = timezone.now()
    suppliers = _suppliers()
    _supplies(suppliers)
    _package_dimensions()
    _deliveries(suppliers)
    customers = _customers()
    for spec in ORDERS:
        _order(spec, customers[spec["customer"]], now)
    _subscription(customers[1], now)
    _email_list(now)
    _support(now)
    _marketing()
