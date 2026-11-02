"""Printable labels as PDF: the label on each pouch or tin (from
catalog.services.label_for) and the stand-in shipping label used without
EasyPost.

The package label's net weight sits at the bottom, in type at least as tall
as 21 CFR 101.105(i) asks for the label's area (taking the label as the
principal display panel), in mixed case, so it is the lower-case "o" that
must be that tall.
"""

import re
from decimal import Decimal

from django.conf import settings

from apps.catalog import services as catalog

from .pdf import Document, text_width, wrap

POINTS = 72
MARGIN = 0.1 * POINTS
# Helvetica's lower-case letters are about this share of the font size tall.
X_HEIGHT = 0.523
SMALLEST_TEXT = 5.5


class LabelError(Exception):
    """The label can't be printed as it is; the message says why."""


def label_size(text=None):
    """(width, height) in inches from "4x2"."""
    match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*", text or settings.PACKAGE_LABEL_SIZE)
    if not match:
        raise LabelError(f"PACKAGE_LABEL_SIZE should look like 4x2 (inches), not {text!r}.")
    return float(match.group(1)), float(match.group(2))


def net_weight_size(width_in, height_in):
    """Font size (points) for the net weight on a label this big."""
    area = width_in * height_in
    for limit, letter_in in ((5, 1 / 16), (25, 1 / 8), (100, 3 / 16), (400, 1 / 4)):
        if area <= limit:
            break
    else:
        letter_in = 1 / 2
    return round(letter_in * POINTS / X_HEIGHT + 0.25, 1)


def package_label_rows(label):
    """[(text, bold)] above the net weight."""
    rows = [(label.name, True)]
    if label.grown_in:
        rows.append((label.grown_in, False))
    if label.ingredients:
        rows.append((f"Ingredients: {label.ingredients}", False))
    if label.contains:
        rows.append((label.contains, True))
    lot = f"Lot {label.lot_code}"
    if label.best_by:
        lot += f"   Best by {label.best_by:%m/%d/%Y}"
    rows.append((lot, False))
    if label.packer:
        rows.append(("Packed by " + ", ".join(line.strip() for line in label.packer.splitlines() if line.strip()),
                     False))
    return rows


def draw_package_label(page, label, width_in, height_in):
    width, height = width_in * POINTS, height_in * POINTS
    usable = width - 2 * MARGIN
    weight_size = net_weight_size(width_in, height_in)
    weight_lines = wrap(label.net_weight, usable, weight_size, bold=True)
    weight_height = len(weight_lines) * weight_size * 1.15
    room = height - 2 * MARGIN - weight_height - 2
    rows = package_label_rows(label)
    size = 10.0
    while True:
        laid = [(line, bold, size + (1.5 if index == 0 else 0))
                for index, (text, bold) in enumerate(rows)
                for line in wrap(text, usable, size + (1.5 if index == 0 else 0), bold)]
        needed = sum(line_size * 1.18 for _, _, line_size in laid)
        if needed <= room or size <= SMALLEST_TEXT:
            break
        size = round(size - 0.25, 2)
    if needed > room:
        raise LabelError(f"The label text for {label.name} does not fit on a {width_in:g}×{height_in:g} in label; "
                         f"use a bigger label (PACKAGE_LABEL_SIZE).")
    y = height - MARGIN
    for line, bold, line_size in laid:
        y -= line_size * 1.0
        page.text(MARGIN, y, line, size=line_size, bold=bold)
        y -= line_size * 0.18
    y = MARGIN + weight_height - weight_size
    for line in weight_lines:
        page.text(MARGIN, y + weight_size * 0.15, line, size=weight_size, bold=True)
        y -= weight_size * 1.15


def package_labels_pdf(packages, size_text=None):
    """One PDF page per packed package (PackedPackage or SoldPackage), at
    the package label size.  Raises LabelError if a label has problems
    (missing facts) or does not fit."""
    width_in, height_in = label_size(size_text)
    doc = Document(width_in * POINTS, height_in * POINTS, title="Package labels")
    for package in packages:
        sold = getattr(package, "sold_package", package)
        if not sold.tea_lot_id:
            continue
        label = catalog.label_for(sold)
        if label.problems:
            raise LabelError(" ".join(label.problems))
        draw_package_label(doc.page(), label, width_in, height_in)
    if not doc.pages:
        raise LabelError("Nothing here needs a package label (only teas packed from bulk do).")
    return doc.render()


def stand_in_shipping_label_pdf(order, tracking_number, service, weight_grams):
    """A 4x6 stand-in for a shipping label (no EasyPost): clearly marked
    not for mailing."""
    doc = Document(4 * POINTS, 6 * POINTS, title=f"Test label {order.number}")
    page = doc.page()
    width = 4 * POINTS
    page.rect(MARGIN, MARGIN, width - 2 * MARGIN, 6 * POINTS - 2 * MARGIN, line_width=2)
    y = 6 * POINTS - 30
    page.text(18, y, "TEST LABEL - NO POSTAGE", size=16, bold=True)
    y -= 16
    page.text(18, y, "Not for mailing", size=10)
    y -= 26
    ship_from = settings.SHIP_FROM
    page.text(18, y, "FROM", size=8, bold=True)
    for line in [ship_from["name"], ship_from["street1"], ship_from["street2"],
                 f"{ship_from['city']}, {ship_from['state']} {ship_from['zip']}".strip(", ")]:
        if line and line.strip():
            y -= 11
            page.text(18, y, line, size=9)
    y -= 28
    page.text(36, y, "SHIP TO", size=9, bold=True)
    for line in order.address_lines():
        y -= 17
        page.text(36, y, line.upper(), size=13, bold=True)
    y -= 34
    page.line(MARGIN, y, width - MARGIN, y, width=1.5)
    y -= 20
    page.text(18, y, service, size=11, bold=True)
    y -= 15
    ounces = (Decimal(weight_grams) / Decimal("28.3495")).quantize(Decimal("0.1"))
    page.text(18, y, f"{ounces} oz   Order {order.number}", size=10)
    y -= 30
    tracking = " ".join(tracking_number[i:i + 4] for i in range(0, len(tracking_number), 4))
    page.text(18, y, "TRACKING #", size=8, bold=True)
    y -= 16
    size = 14
    while text_width(tracking, size, True) > width - 36 and size > 7:
        size -= 1
    page.text(18, y, tracking, size=size, bold=True)
    return doc.render()
