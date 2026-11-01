"""The nine major food allergens US labels must declare (FALCPA, and
sesame from 2023)."""

from django.db import migrations

ALLERGENS = [
    ("milk", "Milk"),
    ("eggs", "Eggs"),
    ("fish", "Fish"),
    ("shellfish", "Crustacean shellfish"),
    ("tree-nuts", "Tree nuts"),
    ("peanuts", "Peanuts"),
    ("wheat", "Wheat"),
    ("soybeans", "Soybeans"),
    ("sesame", "Sesame"),
]


def add_allergens(apps, schema_editor):
    Allergen = apps.get_model("inventory", "Allergen")
    for code, name in ALLERGENS:
        Allergen.objects.get_or_create(code=code, defaults={"name": name})


class Migration(migrations.Migration):
    dependencies = [("inventory", "0001_initial")]

    operations = [migrations.RunPython(add_allergens, migrations.RunPython.noop)]
