from decimal import Decimal

from django import forms
from django.utils import timezone

from apps.catalog.models import Product, SizeOption
from apps.checkout.places import SHIPPING_STATES, ships_to
from apps.inventory.models import Lot

from . import carriers
from .models import BoxSize, Scale

GRAMS_PER = {"g": Decimal(1), "oz": Decimal("28.349523125"), "lb": Decimal("453.59237")}
OTHER_BOX = "other"


class PackForm(forms.Form):
    """One package of an order line: weigh it, pack it, print its label."""

    measured_grams = forms.DecimalField(
        label="Net weight on the scale (g)", min_value=Decimal("0.1"), max_digits=7, decimal_places=1,
        required=False, widget=forms.NumberInput(attrs={"step": "0.1", "inputmode": "decimal"}),
        help_text="Tare the scale with the empty pouch or tin first.  At least the labelled weight.")
    scale = forms.ModelChoiceField(label="Scale", queryset=Scale.objects.none(), required=False, empty_label=None)
    size = forms.ModelChoiceField(label="Tea and size", queryset=SizeOption.objects.none(), required=False,
                                  help_text="What goes in this delivery")
    lot = forms.ModelChoiceField(label="Lot", queryset=Lot.objects.none(), required=False,
                                 empty_label="The oldest usable lot (best-by first)")
    allergens_confirmed = forms.BooleanField(label="Allergen handling done: separate scoop, bench cleaned after",
                                             required=False)

    def __init__(self, *args, line=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.line = line
        size = line.size_option if line else None
        self.fields["scale"].queryset = Scale.objects.filter(is_active=True, seal_intact=True)
        if size is None:
            self.fields["size"].required = True
            self.fields["size"].queryset = SizeOption.objects.filter(
                is_active=True, product__kind=Product.Kind.TEA, product__is_active=True).select_related("product")
        else:
            del self.fields["size"]
        if size is not None and size.product.kind == Product.Kind.TEA:
            self.fields["lot"].queryset = size.tea_lots()
            self.fields["measured_grams"].initial = size.net_grams
        elif size is not None:
            for name in ("measured_grams", "scale", "lot", "allergens_confirmed"):
                del self.fields[name]
        else:
            del self.fields["lot"]

    def clean(self):
        data = super().clean()
        size = (self.line.size_option if self.line else None) or data.get("size")
        if size is not None and size.product.kind == Product.Kind.TEA:
            if data.get("measured_grams") is None:
                self.add_error("measured_grams", "Enter what the scale showed.")
            if not data.get("scale"):
                self.add_error("scale", "Choose the scale (add yours under Fulfillment → Scales in the admin).")
        return data


class UnpackForm(forms.Form):
    note = forms.CharField(label="Why", max_length=200, initial="Packed by mistake")
    reusable = forms.BooleanField(label="The tea and packaging can go back on the shelf", required=False,
                                  initial=True, help_text="Untick if the pouch was sealed or tea was spilled: it is "
                                  "written off as damaged instead.")


class LabelForm(forms.Form):
    box = forms.ChoiceField(label="Box used")
    box_description = forms.CharField(label="Other box: what it is", max_length=120, required=False)
    length_in = forms.DecimalField(label="Length (in)", min_value=Decimal("0.1"), max_digits=5, decimal_places=2,
                                   required=False)
    width_in = forms.DecimalField(label="Width (in)", min_value=Decimal("0.1"), max_digits=5, decimal_places=2,
                                  required=False)
    height_in = forms.DecimalField(label="Height (in)", min_value=Decimal("0.1"), max_digits=5, decimal_places=2,
                                   required=False)
    weight = forms.DecimalField(label="Parcel weight", min_value=Decimal("0.1"), max_digits=8, decimal_places=2,
                                widget=forms.NumberInput(attrs={"step": "0.1", "inputmode": "decimal"}),
                                help_text="On the shipping scale, packed and sealed")
    unit = forms.ChoiceField(label="Unit", choices=[("g", "grams"), ("oz", "ounces"), ("lb", "pounds")])
    service = forms.ChoiceField(label="Service")
    ship_partial = forms.BooleanField(label="Ship what is packed now; back-order the rest", required=False)

    def __init__(self, *args, suggestion=None, service="", **kwargs):
        super().__init__(*args, **kwargs)
        boxes = BoxSize.objects.filter(is_active=True).select_related("item")
        choices = []
        for box in boxes:
            stock = box.item.on_hand()
            note = " (suggested)" if suggestion and suggestion.box == box else ""
            choices.append((str(box.pk), f"{box.item.name}, {box.dimensions_text}{note}, {stock} in stock"))
        self.fields["box"].choices = choices + [(OTHER_BOX, "Another box (describe it below)")]
        if suggestion and suggestion.box:
            self.fields["box"].initial = str(suggestion.box.pk)
            self.fields["weight"].initial = suggestion.parcel_grams()
        elif suggestion:
            self.fields["box"].initial = OTHER_BOX
            self.fields["weight"].initial = suggestion.parcel_grams() or None
        services = carriers.service_choices()
        if service and service not in dict(services):
            services.insert(0, (service, service))
        self.fields["service"].choices = services
        self.fields["service"].initial = service or (services[0][0] if services else "")

    def clean(self):
        data = super().clean()
        box = data.get("box")
        if box == OTHER_BOX:
            data["box"] = None
            if not data.get("box_description"):
                self.add_error("box_description", "Say what box you used.")
            dims = [data.get(name) for name in ("length_in", "width_in", "height_in")]
            if any(dims) and not all(dims):
                self.add_error("length_in", "Give all three sides, or none.")
            data["dimensions"] = dims if all(dims) else None
        elif box:
            data["box"] = BoxSize.objects.filter(pk=box, is_active=True).first()
            if data["box"] is None:
                self.add_error("box", "Choose a box from the list.")
            data["dimensions"] = None
        if data.get("weight") and data.get("unit"):
            data["weight_grams"] = int((data["weight"] * GRAMS_PER[data["unit"]]).to_integral_value())
        return data


class AddressForm(forms.Form):
    name = forms.CharField(label="Name", max_length=100)
    street1 = forms.CharField(label="Street address", max_length=100)
    street2 = forms.CharField(label="Apartment, suite etc.", max_length=100, required=False)
    city = forms.CharField(label="City", max_length=60)
    state = forms.ChoiceField(label="State", choices=[("", "Choose a state")] + SHIPPING_STATES)
    zip = forms.RegexField(label="ZIP code", regex=r"^\d{5}(-\d{4})?$", max_length=10)
    phone = forms.CharField(label="Phone", max_length=30, required=False)
    accept_unverified = forms.BooleanField(label="Use it anyway if the post office does not know it",
                                           required=False)

    def clean(self):
        data = super().clean()
        if data.get("state") and data.get("zip"):
            problem = ships_to(data["state"], data["zip"])
            if problem:
                self.add_error("zip", problem)
        return data


class RefundForm(forms.Form):
    amount = forms.DecimalField(label="Amount ($)", min_value=Decimal("0.01"), max_digits=10, decimal_places=2)
    reason = forms.CharField(label="Why (the customer sees this)", max_length=300,
                             help_text='e.g. "The tin arrived dented" or "Refund of the shipping"')


class CancelForm(forms.Form):
    reason = forms.CharField(label="Why (the customer sees this)", max_length=300,
                             initial="Cancelled at your request")
    reusable = forms.BooleanField(label="Packed tea and packaging can go back on the shelf", required=False,
                                  initial=True)


class ReshipForm(forms.Form):
    reason = forms.CharField(label="Why it is sent again (the customer sees this)", max_length=300,
                             help_text='e.g. "Your parcel was lost in the post, so we have sent it again."')

    def __init__(self, *args, order=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.lines = list(order.lines.all()) if order else []
        for line in self.lines:
            self.fields[f"line_{line.pk}"] = forms.IntegerField(
                label=f"{line.product_name} {line.size_name}".strip(), min_value=0, max_value=line.quantity,
                initial=line.quantity, required=False)

    def quantities(self):
        return {line: self.cleaned_data.get(f"line_{line.pk}") or 0 for line in self.lines}

    def line_fields(self):
        return [self[f"line_{line.pk}"] for line in self.lines]


class BackorderForm(forms.Form):
    expected_on = forms.DateField(label="Stock expected on", required=False,
                                  widget=forms.DateInput(attrs={"type": "date"}))
    reason = forms.CharField(label="Note", max_length=300, initial="Waiting for stock")


class DelayNoticeForm(forms.Form):
    new_ship_by = forms.DateField(label="New ship-by date", widget=forms.DateInput(attrs={"type": "date"}))
    reason = forms.CharField(label="Why (the customer sees this)", max_length=300,
                             help_text='e.g. "Our Assam is on its way from the importer."')

    def clean_new_ship_by(self):
        day = self.cleaned_data["new_ship_by"]
        if day <= timezone.localdate():
            raise forms.ValidationError("Choose a day after today.")
        return day


class PickupForm(forms.Form):
    day = forms.DateField(label="Pickup day", widget=forms.DateInput(attrs={"type": "date"}),
                          help_text="Monday to Saturday.  USPS comes during the usual delivery round.")
    location = forms.CharField(label="Where the parcels will be", max_length=60, initial="Front door")
    instructions = forms.CharField(label="Instructions for the carrier", max_length=200, required=False)


def weight_text(grams):
    ounces = (Decimal(grams) / GRAMS_PER["oz"]).quantize(Decimal("0.1"))
    return f"{grams:,} g ({ounces} oz)"
