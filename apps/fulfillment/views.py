"""The fulfillment pages: the order queue, packing list, one order's page
(pack, label, ship, cancel, refund, reship, delay notice), USPS pickups,
and the installable web app's manifest and service worker.  Plus the
customer's answer to a delay notice."""

from datetime import timedelta

from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import cache_control, never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.audit.models import AuditEvent
from apps.checkout.models import Order
from apps.checkout.shipping import Address
from apps.core.decorators import owner_required
from apps.inventory import services as inventory

from . import forms, labels, services
from .models import DelayNotice, PackedPackage, Parcel, Pickup, PostageLabel


def _errors(request, exc):
    for message in getattr(exc, "messages", [str(exc)]):
        messages.error(request, message)


def _order_url(order, anchor=""):
    return reverse("fulfillment:order", args=[order.number]) + (f"#{anchor}" if anchor else "")


def ship_status(order, today=None):
    """("late" | "due" | "ok", text) for the order's promised ship date."""
    today = today or timezone.localdate()
    if not order.ship_by:
        return "ok", ""
    if order.ship_by < today:
        days = (today - order.ship_by).days
        return "late", f"Late: promised {order.ship_by:%a %b %-d} ({days} day{'s' if days != 1 else ''} ago)"
    if order.ship_by <= today + timedelta(days=1):
        return "due", f"Ship by {'today' if order.ship_by == today else 'tomorrow'}"
    return "ok", f"Ship by {order.ship_by:%a %b %-d}"


def _row(order, today):
    """What the queue shows for one order."""
    active = services.active_parcels(order)
    packed = needed = 0
    allergens = set()
    for parcel in active:
        for row in services.progress(parcel):
            packed += len(row.packed)
            needed += len(row.packed) + row.remaining
            if row.size is not None and row.remaining:
                allergens.update(services.allergens_of(services.likely_lot(row.size)))
            for package in row.packed:
                allergens.update(services.allergens_of(package.sold_package.tea_lot))
    status, text = ship_status(order, today)
    return {
        "order": order, "status": status, "status_text": text, "packed": packed, "needed": needed,
        "allergens": sorted(allergens),
        "backordered": any(parcel.status == Parcel.Status.BACKORDERED for parcel in active),
        "waiting_only": bool(active) and all(parcel.status == Parcel.Status.BACKORDERED for parcel in active),
        "reship": any(parcel.kind == Parcel.Kind.RESHIP for parcel in active),
        "items": sum(line.quantity for line in order.lines.all()),
        "awaiting_consent": any(notice.awaiting_consent for notice in order.delay_notices.all()),
    }


@never_cache
@owner_required
@require_GET
def queue(request):
    """Orders to pack, soonest promised first; allergen teas after the
    others due the same day, as they should be packed last."""
    today = timezone.localdate()
    show = request.GET.get("show", "to_pack")
    if show == "shipped":
        orders = Order.objects.filter(status=Order.Status.SHIPPED, shipped_at__gte=timezone.now() - timedelta(days=14))
        rows = [_row(order, today) for order in orders.order_by("-shipped_at").prefetch_related("lines")[:100]]
    else:
        orders = Order.objects.filter(
            Q(status=Order.Status.PAID) | Q(parcels__status__in=Parcel.ACTIVE_STATUSES, status=Order.Status.SHIPPED)
        ).distinct().prefetch_related("lines", "delay_notices")
        rows = [_row(order, today) for order in orders]
        if show == "backordered":
            rows = [row for row in rows if row["backordered"]]
        else:
            rows = [row for row in rows if not row["waiting_only"]]
        rows.sort(key=lambda row: (row["order"].ship_by or today, bool(row["allergens"]), row["order"].paid_at
                                   or row["order"].created_at))
    counts = {
        "late": sum(1 for row in rows if row["status"] == "late"),
        "due": sum(1 for row in rows if row["status"] == "due"),
    }
    return render(request, "fulfillment/queue.html", {
        "rows": rows, "show": show, "counts": counts,
        "waiting_pickup": services.labels_for_pickup().count(),
    })


@never_cache
@owner_required
@require_GET
def packing_list(request):
    """Every package still to pack, by tea and size, allergen teas last."""
    groups = {}
    orders = Order.objects.filter(
        Q(status=Order.Status.PAID) | Q(parcels__status=Parcel.Status.OPEN, status=Order.Status.SHIPPED)).distinct()
    open_parcels = [parcel for order in orders.order_by("ship_by", "pk") for parcel in services.parcels(order)
                    if parcel.status == Parcel.Status.OPEN]
    for parcel in open_parcels:
        for row in services.progress(parcel):
            if row.size is None:
                key = ("subscription", row.order_line.product_name)
                group = groups.setdefault(key, {"name": row.order_line.product_name, "size": None, "count": 0,
                                                "orders": [], "allergens": [], "lot": None, "grams": 0})
                if row.remaining:
                    group["count"] += 1
                    group["orders"].append(parcel.order)
                continue
            if not row.remaining:
                continue
            group = groups.setdefault(row.size.pk, {"name": str(row.size), "size": row.size, "count": 0,
                                                    "orders": [], "allergens": [], "lot": None, "grams": 0})
            if group["lot"] is None:
                group["lot"] = services.likely_lot(row.size)
                group["allergens"] = services.allergens_of(group["lot"])
            group["count"] += row.remaining
            group["grams"] += (row.size.net_grams or 0) * row.remaining
            group["orders"].append(parcel.order)
    rows = sorted(groups.values(), key=lambda g: (bool(g["allergens"]), g["name"]))
    return render(request, "fulfillment/packing_list.html", {
        "rows": rows, "plain": [g for g in rows if not g["allergens"]], "allergen": [g for g in rows if g["allergens"]],
        "today": timezone.localdate(),
    })


def _parcel_context(parcel, request):
    rows = services.progress(parcel)
    lines = []
    for row in rows:
        prefix = f"p{parcel.pk}-l{row.order_line.pk}"
        lot = services.likely_lot(row.size) if row.size is not None else None
        allergens = services.allergens_of(lot)
        lines.append({
            "row": row, "form": forms.PackForm(line=row.order_line, prefix=prefix), "lot": lot,
            "allergens": allergens,
            "url": reverse("fulfillment:pack", args=[parcel.pk, row.order_line.pk]),
        })
    label = parcel.current_label()
    suggestion = services.suggest_box(parcel) if parcel.is_active and not label else None
    return {
        "parcel": parcel, "lines": lines, "label": label, "suggestion": suggestion,
        "past_labels": parcel.labels.exclude(voided_at=None),
        "label_form": forms.LabelForm(prefix=f"label{parcel.pk}", suggestion=suggestion,
                                      service=parcel.order.shipping_service) if suggestion else None,
        "backorder_form": forms.BackorderForm(prefix=f"bo{parcel.pk}") if parcel.status == Parcel.Status.OPEN else None,
        "tea_packed": [p for row in rows for p in row.packed if p.sold_package.tea_lot_id],
        "all_packed": all(row.done for row in rows),
        "any_packed": any(row.packed for row in rows),
    }


@never_cache
@owner_required
@require_GET
def order_detail(request, number):
    order = get_object_or_404(Order.objects.prefetch_related("lines"), number=number)
    if order.status == Order.Status.PENDING:
        raise Http404("Not paid")
    parcels = [_parcel_context(parcel, request) for parcel in services.parcels(order)]
    status, status_text = ship_status(order)
    print_ids = [int(pk) for pk in request.GET.get("print", "").split(",") if pk.isdigit()]
    to_print = list(PackedPackage.objects.filter(pk__in=print_ids, parcel__order=order))
    events = AuditEvent.objects.filter(object_type="checkout.order", object_id=str(order.pk)).order_by(
        "-timestamp")[:40]
    today = timezone.localdate()
    return render(request, "fulfillment/order.html", {
        "order": order, "parcels": parcels, "status": status, "status_text": status_text,
        "active": [p for p in parcels if p["parcel"].is_active],
        "shipped": [p for p in parcels if p["parcel"].status == Parcel.Status.SHIPPED],
        "to_print": to_print,
        "refunds": order.refunds.all(), "refunded": services.refunded(order), "refundable": services.refundable(order),
        "notices": order.delay_notices.all(),
        "refund_form": forms.RefundForm(prefix="refund", order=order),
        "cancel_form": forms.CancelForm(prefix="cancel"),
        "delay_form": forms.DelayNoticeForm(prefix="delay", initial={"new_ship_by": max(order.ship_by or today, today)
                                                                     + timedelta(days=7)}),
        "can_cancel": order.status == Order.Status.PAID and not any(
            p["parcel"].status == Parcel.Status.SHIPPED or p["label"] for p in parcels),
        "can_reship": order.status in Order.PAID_STATUSES and any(
            p["parcel"].status == Parcel.Status.SHIPPED for p in parcels),
        "events": events,
        "unpack_form": forms.UnpackForm(prefix="unpack"),
    })


def _parcel(pk):
    return get_object_or_404(Parcel.objects.select_related("order"), pk=pk)


@owner_required
@require_POST
def pack(request, parcel_pk, line_pk):
    parcel = _parcel(parcel_pk)
    line = get_object_or_404(parcel.order.lines, pk=line_pk)
    form = forms.PackForm(request.POST, line=line, prefix=f"p{parcel.pk}-l{line.pk}")
    if not form.is_valid():
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
        return redirect(_order_url(parcel.order, f"parcel-{parcel.pk}"))
    data = form.cleaned_data
    try:
        packed = services.pack_package(
            parcel, line, measured_grams=data.get("measured_grams"), scale=data.get("scale"), user=request.user,
            lot=data.get("lot"), size=data.get("size"), allergens_confirmed=data.get("allergens_confirmed", False))
    except (ValidationError, inventory.StockError) as exc:
        _errors(request, exc)
        return redirect(_order_url(parcel.order, f"parcel-{parcel.pk}"))
    sold = packed.sold_package
    if sold.tea_lot_id:
        messages.success(request, f"Packed {sold.size_option}: {packed.measured_grams} g from lot {sold.tea_lot.code}."
                                  "  Print its label now.")
        return redirect(reverse("fulfillment:order", args=[parcel.order.number]) + f"?print={packed.pk}#print")
    messages.success(request, f"Packed {sold.size_option}.")
    return redirect(_order_url(parcel.order, f"parcel-{parcel.pk}"))


@owner_required
@require_POST
def unpack(request, pk):
    package = get_object_or_404(PackedPackage.objects.select_related("parcel__order", "sold_package"), pk=pk)
    form = forms.UnpackForm(request.POST, prefix="unpack")
    note = form.cleaned_data["note"] if form.is_valid() else "Packed by mistake"
    reusable = form.cleaned_data.get("reusable", False) if form.is_valid() else True
    try:
        services.unpack(package, note, reusable=reusable, user=request.user)
    except (ValidationError, ValueError) as exc:
        _errors(request, exc)
    else:
        messages.success(request, f"Unpacked {package.sold_package.size_option}; "
                         + ("its tea and packaging are back in stock." if reusable else "written off as damaged."))
    return redirect(_order_url(package.parcel.order, f"parcel-{package.parcel.pk}"))


def _pdf_response(content, filename):
    response = HttpResponse(content, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response


@never_cache
@owner_required
@require_GET
def package_labels(request, parcel_pk):
    """The labels of a parcel's tea packages as one PDF (?packages=1,2 for
    some of them)."""
    parcel = _parcel(parcel_pk)
    packages = list(parcel.live_packages())
    wanted = [int(pk) for pk in request.GET.get("packages", "").split(",") if pk.isdigit()]
    if wanted:
        packages = [p for p in packages if p.pk in wanted]
    try:
        content = labels.package_labels_pdf(packages)
    except labels.LabelError as exc:
        messages.error(request, f"Can't print the label: {exc}")
        return redirect(_order_url(parcel.order, f"parcel-{parcel.pk}"))
    services.mark_labels_printed(packages)
    return _pdf_response(content, f"labels-{parcel.order.number}.pdf")


@owner_required
@require_POST
def buy_label(request, parcel_pk):
    parcel = _parcel(parcel_pk)
    suggestion = services.suggest_box(parcel)
    form = forms.LabelForm(request.POST, prefix=f"label{parcel.pk}", suggestion=suggestion,
                           service=parcel.order.shipping_service)
    if not form.is_valid():
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
        return redirect(_order_url(parcel.order, f"parcel-{parcel.pk}"))
    data = form.cleaned_data
    try:
        label, warnings = services.buy_label(
            parcel, weight_grams=data["weight_grams"], service=data["service"], box=data.get("box"),
            box_description=data.get("box_description", ""), dimensions=data.get("dimensions"), user=request.user,
            ship_partial=data.get("ship_partial", False), suggested=suggestion.box)
    except (ValidationError, inventory.StockError) as exc:
        _errors(request, exc)
        return redirect(_order_url(parcel.order, f"parcel-{parcel.pk}"))
    for warning in warnings:
        messages.warning(request, warning)
    messages.success(request, f"Label bought: {label.service}, tracking {label.tracking_number}"
                     + (" (a test label: don't mail it)" if label.test_mode else "")
                     + ".  The customer has the tracking number.")
    return redirect(_order_url(parcel.order, f"parcel-{parcel.pk}"))


@never_cache
@owner_required
@require_GET
def shipping_label(request, pk):
    label = get_object_or_404(PostageLabel.objects.select_related("parcel__order"), pk=pk)
    if not label.label_file:
        raise Http404("No label file")
    if not label.printed_at:
        PostageLabel.objects.filter(pk=label.pk).update(printed_at=timezone.now())
    extension = "zpl" if label.label_format == "ZPL" else "pdf"
    return FileResponse(label.label_file.open("rb"), as_attachment=label.label_format == "ZPL",
                        filename=f"shipping-label-{label.parcel.order.number}.{extension}",
                        content_type="application/pdf" if extension == "pdf" else "application/octet-stream")


@owner_required
@require_POST
def void_label(request, pk):
    label = get_object_or_404(PostageLabel.objects.select_related("parcel__order"), pk=pk)
    try:
        services.void_label(label, user=request.user)
    except ValidationError as exc:
        _errors(request, exc)
    else:
        messages.success(request, f"Label {label.tracking_number} voided; the postage refund is "
                         f"{label.void_status or 'asked for'}.  The box is back in stock.")
    return redirect(_order_url(label.parcel.order, f"parcel-{label.parcel.pk}"))


@never_cache
@owner_required
@require_http_methods(["GET", "POST"])
def change_address(request, number):
    order = get_object_or_404(Order, number=number)
    if request.method == "POST":
        form = forms.AddressForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            address = Address(**{name: data.get(name, "") for name in Order.ADDRESS_FIELDS})
            try:
                checked = services.change_address(order, address, accept_unverified=data["accept_unverified"],
                                                  user=request.user)
            except ValidationError as exc:
                _errors(request, exc)
            else:
                messages.success(request, "Address changed" + ("" if checked.ok else " (not confirmed by the post "
                                                               "office)") + ".")
                return redirect(_order_url(order))
    else:
        form = forms.AddressForm(initial={name: getattr(order, f"ship_{name}") for name in Order.ADDRESS_FIELDS})
    return render(request, "fulfillment/address.html", {"order": order, "form": form})


@owner_required
@require_POST
def refund(request, number):
    order = get_object_or_404(Order, number=number)
    form = forms.RefundForm(request.POST, prefix="refund", order=order)
    if form.is_valid():
        try:
            done = services.refund(order, form.cleaned_data["amount"], form.cleaned_data["reason"], user=request.user,
                                   items=form.items(), shipping=form.cleaned_data.get("shipping", False))
        except (ValidationError, PermissionDenied) as exc:
            _errors(request, exc)
        else:
            messages.success(request, f"Refunded ${done.amount:,.2f}; the customer has been told.")
    else:
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
    return redirect(_order_url(order, "money"))


@owner_required
@require_POST
def cancel(request, number):
    order = get_object_or_404(Order, number=number)
    form = forms.CancelForm(request.POST, prefix="cancel")
    if form.is_valid():
        try:
            amount = services.cancel_order(order, form.cleaned_data["reason"], user=request.user,
                                           reusable=form.cleaned_data["reusable"])
        except (ValidationError, PermissionDenied) as exc:
            _errors(request, exc)
        else:
            messages.success(request, f"Order {order.number} cancelled and ${amount:,.2f} refunded; packed stock is "
                             "back and the customer has been told.")
    else:
        messages.error(request, "Say why the order is cancelled.")
    return redirect(_order_url(order))


@never_cache
@owner_required
@require_http_methods(["GET", "POST"])
def reship(request, number):
    order = get_object_or_404(Order, number=number)
    form = forms.ReshipForm(request.POST or None, order=order)
    if request.method == "POST" and form.is_valid():
        try:
            parcel = services.start_reship(order, form.quantities(), form.cleaned_data["reason"], user=request.user)
        except ValidationError as exc:
            _errors(request, exc)
        else:
            messages.success(request, "Reship started: pack it and buy its label below.  The customer pays nothing.")
            return redirect(_order_url(order, f"parcel-{parcel.pk}"))
    return render(request, "fulfillment/reship.html", {"order": order, "form": form})


@owner_required
@require_POST
def backorder(request, parcel_pk):
    parcel = _parcel(parcel_pk)
    if request.POST.get("resume"):
        services.resume(parcel)
        messages.success(request, "Back to packing.")
        return redirect(_order_url(parcel.order, f"parcel-{parcel.pk}"))
    form = forms.BackorderForm(request.POST, prefix=f"bo{parcel.pk}")
    if form.is_valid():
        try:
            services.backorder(parcel, form.cleaned_data["expected_on"], form.cleaned_data["reason"])
        except ValidationError as exc:
            _errors(request, exc)
        else:
            order = parcel.order
            if form.cleaned_data["expected_on"] and order.ship_by and form.cleaned_data["expected_on"] >= order.ship_by:
                messages.warning(request, "That is after the promised ship date: send the customer a delay notice "
                                 "(the Mail Order Rule).")
            else:
                messages.success(request, "Marked back-ordered.")
    return redirect(_order_url(parcel.order, f"parcel-{parcel.pk}"))


@owner_required
@require_POST
def delay_notice(request, number):
    order = get_object_or_404(Order, number=number)
    form = forms.DelayNoticeForm(request.POST, prefix="delay")
    if form.is_valid():
        try:
            notice = services.send_delay_notice(order, form.cleaned_data["new_ship_by"], form.cleaned_data["reason"],
                                                user=request.user)
        except ValidationError as exc:
            _errors(request, exc)
        else:
            # The email is queued (apps.jobs); a failure is retried and shows
            # on the dashboard.
            if notice.needs_consent:
                messages.success(request, f"Delay notice sent.  The customer must agree to wait; if they have not "
                                 f"by {notice.answer_by:%B %-d}, cancel and refund the order.")
            else:
                messages.success(request, f"Delay notice sent; the order now ships by {notice.new_ship_by:%B %-d} "
                                 "unless the customer cancels.")
    else:
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
    return redirect(_order_url(order, "delay"))


@never_cache
@owner_required
@require_http_methods(["GET", "POST"])
def pickups(request):
    if request.method == "POST":
        form = forms.PickupForm(request.POST)
        if form.is_valid():
            try:
                pickup = services.schedule_pickup(form.cleaned_data["day"], location=form.cleaned_data["location"],
                                                  instructions=form.cleaned_data["instructions"], user=request.user)
            except ValidationError as exc:
                _errors(request, exc)
            else:
                messages.success(request, f"USPS pickup booked for {pickup.pickup_date:%A, %B %-d}: confirmation "
                                 f"{pickup.confirmation}.")
                return redirect("fulfillment:pickups")
    else:
        form = forms.PickupForm(initial={"day": services.next_pickup_day()})
    upcoming = Pickup.objects.filter(pickup_date__gte=timezone.localdate(), status=Pickup.Status.SCHEDULED)
    return render(request, "fulfillment/pickups.html", {
        "form": form, "waiting": list(services.labels_for_pickup()), "upcoming": upcoming,
        "past": Pickup.objects.exclude(pk__in=upcoming)[:10],
    })


@owner_required
@require_POST
def pickup_action(request, pk):
    pickup = get_object_or_404(Pickup, pk=pk)
    if request.POST.get("action") == "add":
        count = services.add_to_pickup(pickup)
        messages.success(request, f"Added {count} parcel{'s' if count != 1 else ''} to the pickup.")
    else:
        try:
            services.cancel_pickup(pickup)
        except ValidationError as exc:
            _errors(request, exc)
        else:
            messages.success(request, "Pickup cancelled.")
    return redirect("fulfillment:pickups")


# -- The installable web app ---------------------------------------------------

@require_GET
@cache_control(max_age=3600)
def manifest(request):
    content = render_to_string("fulfillment/manifest.webmanifest", {}, request=request)
    return HttpResponse(content, content_type="application/manifest+json")


@require_GET
@cache_control(no_cache=True)
def service_worker(request):
    content = render_to_string("fulfillment/sw.js", {})
    response = HttpResponse(content, content_type="text/javascript")
    response["Service-Worker-Allowed"] = reverse("fulfillment:queue")
    return response


@require_GET
def offline(request):
    return render(request, "fulfillment/offline.html")


# -- The customer's answer to a delay notice ------------------------------------

@never_cache
@require_http_methods(["GET", "POST"])
def delay_answer(request, token, pk):
    order = get_object_or_404(Order, token=token)
    notice = get_object_or_404(DelayNotice, pk=pk, order=order)
    if request.method == "POST":
        choice = request.POST.get("choice")
        if choice in ("wait", "cancel"):
            try:
                services.answer_delay(notice, wait=choice == "wait")
            except ValidationError as exc:
                _errors(request, exc)
            else:
                return redirect("fulfillment:delay_answer", token=token, pk=pk)
    order.refresh_from_db()
    notice.refresh_from_db()
    return render(request, "fulfillment/delay_answer.html", {
        "order": order, "notice": notice, "refundable": services.refundable(order),
        "can_answer": order.status == Order.Status.PAID,
    })

