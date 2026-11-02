"""The support agent's tools.  All read-only, and scoped to what the
customer may see: an order only with its number and the email on it, never
the address, payment or anyone else's orders.  The model's choice of input
is untrusted, so each tool checks for itself.

reply and escalate are the agent's two ways to finish (final tools); the
code in agent.py checks a reply before anything goes out.
"""

import re

from django.db.models import Q
from django.urls import reverse

from apps.agents.runner import Tool, string
from apps.catalog.models import Product
from apps.checkout.models import CheckoutSettings, Order
from apps.checkout.emails import absolute

from .models import ANSWERABLE, Conversation

ORDER_NUMBER_RE = re.compile(r"\b\d{6}-[A-HJ-NP-Z2-9]{4}\b", re.IGNORECASE)

# USPS's own published times in transit, in working days.
USUAL_TRANSIT = {
    "USPS Ground Advantage": "2-5 working days",
    "USPS Priority Mail": "1-3 working days",
    "USPS Priority Mail Express": "1-2 days",
}

NOT_FOUND = {"found": False,
             "note": "No order with that number has the email address this customer gave.  Don't say whether the "
                     "number exists; ask them to check it, or hand the conversation to the owner."}


def _order(conversation, order_number):
    number = str(order_number).strip().upper()
    if not ORDER_NUMBER_RE.fullmatch(number):
        return None
    order = Order.objects.filter(number=number, email__iexact=conversation.email).first()
    if order is not None and conversation.order_id != order.pk:
        Conversation.objects.filter(pk=conversation.pk).update(order=order)
        conversation.order = order
    return order


def lookup_order(conversation, order_number):
    order = _order(conversation, order_number)
    if order is None:
        return NOT_FOUND
    backordered = [{"expected_on": parcel.expected_on.isoformat() if parcel.expected_on else None}
                   for parcel in order.parcels.filter(status="backordered")]
    return {
        "found": True,
        "number": order.number,
        "status": order.get_status_display(),
        "placed_on": order.created_at.date().isoformat(),
        "paid": order.is_paid,
        "promised_to_ship_by": order.ship_by.isoformat() if order.ship_by else None,
        "shipped_on": order.shipped_at.date().isoformat() if order.shipped_at else None,
        "shipping_service": order.shipping_service,
        "tracking_number": order.tracking_number or None,
        "tracking_link": order.tracking_url() or None,
        "items": [f"{line.quantity} x {line.product_name}" + (f" ({line.size_name})" if line.size_name else "")
                  for line in order.lines.all()],
        "back_ordered_parts": backordered,
        "order_page": absolute(order.get_absolute_url()),
    }


def track_parcel(conversation, order_number):
    order = _order(conversation, order_number)
    if order is None:
        return NOT_FOUND
    parcels = []
    for parcel in order.parcels.all():
        label = parcel.current_label()
        parcels.append({
            "kind": parcel.get_kind_display(), "status": parcel.get_status_display(),
            "shipped_on": parcel.shipped_at.date().isoformat() if parcel.shipped_at else None,
            "carrier": label.carrier if label else None, "service": label.service if label else None,
            "tracking_number": label.tracking_number if label and not label.test_mode else None,
            "expected_on": parcel.expected_on.isoformat() if parcel.expected_on else None,
        })
    for parcel in parcels:
        if parcel["tracking_number"] and (parcel["carrier"] or "").upper() == "USPS":
            parcel["tracking_link"] = ("https://tools.usps.com/go/TrackConfirmAction?tLabels="
                                       + parcel["tracking_number"])
    return {"found": True, "number": order.number, "status": order.get_status_display(), "parcels": parcels,
            "tracking_number": order.tracking_number or None, "tracking_link": order.tracking_url() or None,
            "note": "Tracking updates come from USPS; the shop can't see more than the tracking page shows."}


def _fahrenheit(celsius):
    return round(celsius * 9 / 5 + 32)


def product_facts(product):
    brewing = {
        "water_temperature": f"{product.brew_temp_c} °C ({_fahrenheit(product.brew_temp_c)} °F)"
        if product.brew_temp_c else None,
        "steeping_time": product.brew_minutes or None,
        "grams_per_250ml_cup": str(product.brew_grams) if product.brew_grams else None,
        "infusions": product.brew_infusions,
        "notes": product.brew_notes or None,
    }
    return {
        "name": product.name,
        "what_it_is": product.label_name or product.get_kind_display(),
        "summary": product.summary,
        "caffeine": product.get_caffeine_display() if product.caffeine else None,
        "brewing": brewing if product.kind == Product.Kind.TEA else None,
        "sizes": [{"size": size.name, "price": f"${size.price}", "in_stock": size.packages_available() > 0}
                  for size in product.shop_sizes()],
        "page": absolute(product.get_absolute_url()),
    }


def search_catalog(conversation, query):
    words = [word for word in re.findall(r"[\w'-]+", str(query).lower()) if len(word) >= 3][:8]
    if not words:
        return {"products": [], "note": "Give a tea's name or a few words about it."}
    match = Q()
    for word in words:
        match |= (Q(name__icontains=word) | Q(label_name__icontains=word) | Q(summary__icontains=word)
                  | Q(category__name__icontains=word))
    products = list(Product.objects.filter(match, is_active=True).select_related("category").distinct()[:40])

    def score(product):
        text = " ".join([product.name, product.label_name, product.summary,
                         product.category.name if product.category_id else ""]).lower()
        return (sum(word in product.name.lower() for word in words) * 3 + sum(word in text for word in words))

    products.sort(key=score, reverse=True)
    return {"products": [product_facts(product) for product in products[:3]]}


def shipping_info(conversation):
    shop = CheckoutSettings.current()
    return {
        "ships_within": f"{shop.ship_within_days} working day{'s' if shop.ship_within_days != 1 else ''} of payment",
        "away_now": shop.on_vacation(),
        "away_message": shop.vacation_message or None,
        "ships_again_from": shop.vacation_ships_from.isoformat() if shop.on_vacation() and shop.vacation_ships_from
        else None,
        "taking_orders": shop.taking_orders(),
        "free_shipping_from": f"${shop.free_shipping_over}" if shop.free_shipping_over is not None else None,
        "where": "The 48 contiguous US states and DC, by USPS.  Not yet Alaska, Hawaii, territories, APO/FPO "
                 "addresses or abroad.",
        "usual_time_in_transit_after_shipping": USUAL_TRANSIT,
        "tracking": "The tracking number is emailed when the parcel ships.",
        "cost": "The live USPS price for the parcel, shown at checkout; no handling charge.",
        "policy_page": absolute(reverse("storefront:policy", args=["shipping"])),
    }


def make_tools(conversation):
    def bound(fn):
        return lambda **kwargs: fn(conversation, **kwargs)

    order_number = string("The order number the customer gave, like 261101-AB2C")
    return [
        Tool("lookup_order", "An order's status, items, promised ship date and tracking.  Needs the order number; "
             "it is found only if the order's email matches this customer's.", bound(lookup_order),
             {"order_number": order_number}, ("order_number",)),
        Tool("track_parcel", "The parcels of an order and their tracking numbers.", bound(track_parcel),
             {"order_number": order_number}, ("order_number",)),
        Tool("search_catalog", "Teas and goods in the shop matching some words, with brewing advice, caffeine, "
             "sizes and prices.", bound(search_catalog),
             {"query": string("A tea's name or words about it")}, ("query",)),
        Tool("shipping_info", "How soon orders ship, where to, the usual USPS times in transit, free shipping, "
             "and whether the shop is away.", bound(shipping_info)),
        Tool("reply", "Answer the customer.  Only for order status, brewing advice or shipping times, and only "
             "with facts from the tools.", None,
             {"category": string("What the question is about", enum=[str(c) for c in ANSWERABLE]),
              "text": string("The reply to the customer, plain text, no greeting line with their name")},
             ("category", "text"), final=True),
        Tool("escalate", "Hand the conversation to a person at the shop.  The customer is told someone will get "
             "back to them.", None, {"reason": string("Why, in a short line for the owner")}, ("reason",),
             final=True),
    ]
