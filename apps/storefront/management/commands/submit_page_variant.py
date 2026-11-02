"""Propose a design for a tea's page, as an AI agent (or anyone) would.

    python manage.py submit_page_variant variant.json --agent design-agent

variant.json holds one design or a list of them::

    {"product": "assam-halmari", "palette": "bark", "motif": "bird",
     "layout": "story", "headline": "Malty and bright",
     "story": "Picked in the second flush ...", "rationale": "Warm browns suit its malty cup."}

palette, motif and layout must be names from apps/core/design.py, so
designs stay within the shop's theme.  Copy is checked like all product
copy (no health claims, caffeine-free only when true, protected origins
only when certified).  Each design is saved as a draft waiting for the
owner's approval on the dashboard; nothing goes live from here.  Exits
with an error, saving nothing, if any design fails the checks.
"""

import json

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.audit import acting_as_agent, record
from apps.catalog.models import Product
from apps.storefront.models import PageVariant

FIELDS = ("palette", "motif", "layout", "headline", "story", "rationale")


def build_variant(data, agent):
    if not isinstance(data, dict):
        raise ValidationError("Each design must be a JSON object.")
    unknown = set(data) - set(FIELDS) - {"product"}
    if unknown:
        raise ValidationError(f"Unknown fields: {', '.join(sorted(unknown))}")
    try:
        product = Product.objects.get(slug=data.get("product", ""))
    except Product.DoesNotExist:
        raise ValidationError(f"No product with slug {data.get('product')!r}.") from None
    variant = PageVariant(product=product, made_by=agent, **{name: data.get(name, "") for name in FIELDS})
    if not variant.layout:
        variant.layout = "classic"
    variant.full_clean()
    return variant


class Command(BaseCommand):
    help = "Save proposed page designs as drafts for the owner to approve."

    def add_arguments(self, parser):
        parser.add_argument("path", help="JSON file with one design or a list of designs ('-' for standard input)")
        parser.add_argument("--agent", default="design-agent", help="Who proposes them (default design-agent)")

    def handle(self, path, agent, **options):
        try:
            if path == "-":
                import sys

                payload = json.load(sys.stdin)
            else:
                with open(path, encoding="utf-8") as file:
                    payload = json.load(file)
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f"Cannot read {path}: {exc}") from exc
        designs = payload if isinstance(payload, list) else [payload]
        errors = []
        variants = []
        for number, data in enumerate(designs, start=1):
            try:
                variants.append(build_variant(data, agent))
            except ValidationError as exc:
                detail = "; ".join(f"{k}: {' '.join(v)}" for k, v in exc.message_dict.items()) if hasattr(
                    exc, "error_dict") else " ".join(exc.messages)
                errors.append(f"Design {number}: {detail}")
        if errors:
            raise CommandError("Nothing saved.\n" + "\n".join(errors))
        with acting_as_agent(agent), transaction.atomic():
            for variant in variants:
                variant.save()
                record("storefront.variant_proposed", obj=variant,
                       message=f"Proposed a page design for {variant.product}; waiting for the owner's approval")
        self.stdout.write(self.style.SUCCESS(f"{len(variants)} design(s) saved, waiting for the owner's approval."))
