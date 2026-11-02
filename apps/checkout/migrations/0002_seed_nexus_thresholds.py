"""Starting economic-nexus thresholds for remote sellers, by state.

A summary as of late 2025; states change these.  Check a state's own
guidance when the dashboard warns about it, and correct the row in the
admin (Checkout → Nexus thresholds).
"""

from decimal import Decimal

from django.db import migrations

K100, K250, K500 = Decimal("100000"), Decimal("250000"), Decimal("500000")
NO_SALES_TAX = ["DE", "MT", "NH", "OR"]
# state: (sales, transactions or None, both needed)
THRESHOLDS = {
    "AL": (K250, None, False), "AZ": (K100, None, False), "AR": (K100, 200, False), "CA": (K500, None, False),
    "CO": (K100, None, False), "CT": (K100, 200, True), "DC": (K100, 200, False), "FL": (K100, None, False),
    "GA": (K100, 200, False), "ID": (K100, None, False), "IL": (K100, None, False), "IN": (K100, None, False),
    "IA": (K100, None, False), "KS": (K100, None, False), "KY": (K100, 200, False), "LA": (K100, None, False),
    "ME": (K100, None, False), "MD": (K100, 200, False), "MA": (K100, None, False), "MI": (K100, 200, False),
    "MN": (K100, 200, False), "MS": (K250, None, False), "MO": (K100, None, False), "NE": (K100, 200, False),
    "NV": (K100, 200, False), "NJ": (K100, 200, False), "NM": (K100, None, False), "NY": (K500, 100, True),
    "NC": (K100, None, False), "ND": (K100, None, False), "OH": (K100, 200, False), "OK": (K100, None, False),
    "PA": (K100, None, False), "RI": (K100, 200, False), "SC": (K100, None, False), "SD": (K100, None, False),
    "TN": (K100, None, False), "TX": (K500, None, False), "UT": (K100, None, False), "VT": (K100, 200, False),
    "VA": (K100, 200, False), "WA": (K100, None, False), "WV": (K100, 200, False), "WI": (K100, None, False),
    "WY": (K100, None, False),
}


def seed(apps, schema_editor):
    NexusThreshold = apps.get_model("checkout", "NexusThreshold")
    for state in NO_SALES_TAX:
        NexusThreshold.objects.get_or_create(state=state, defaults={"has_sales_tax": False,
                                                                    "notes": "No statewide sales tax"})
    for state, (sales, transactions, both) in THRESHOLDS.items():
        NexusThreshold.objects.get_or_create(state=state, defaults={
            "sales": sales, "transactions": transactions, "needs_both": both,
            "notes": "Starting figure; check the state's guidance"})


class Migration(migrations.Migration):
    dependencies = [("checkout", "0001_initial")]

    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
