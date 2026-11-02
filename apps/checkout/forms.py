from django import forms
from django.conf import settings

from .places import SHIPPING_STATES, ships_to
from .shipping import Address


class AddressForm(forms.Form):
    """Email and a shipping address in the 48 contiguous states or DC."""

    email = forms.EmailField(
        label="Email", max_length=254,
        help_text="For your receipt and shipping updates.  No marketing unless you ask for it.",
        widget=forms.EmailInput(attrs={"autocomplete": "email"}))
    name = forms.CharField(label="Full name", max_length=100,
                           widget=forms.TextInput(attrs={"autocomplete": "shipping name"}))
    street1 = forms.CharField(label="Street address", max_length=100,
                              widget=forms.TextInput(attrs={"autocomplete": "shipping address-line1"}))
    street2 = forms.CharField(label="Apartment, suite, etc. (optional)", max_length=100, required=False,
                              widget=forms.TextInput(attrs={"autocomplete": "shipping address-line2"}))
    city = forms.CharField(label="City", max_length=60,
                           widget=forms.TextInput(attrs={"autocomplete": "shipping address-level2"}))
    state = forms.ChoiceField(label="State", choices=[("", "Choose a state")] + SHIPPING_STATES,
                              help_text="We ship to the 48 contiguous states and DC.",
                              widget=forms.Select(attrs={"autocomplete": "shipping address-level1"}))
    zip = forms.RegexField(label="ZIP code", regex=r"^\d{5}(-\d{4})?$", max_length=10,
                           error_messages={"invalid": "Enter a 5-digit ZIP code (or ZIP+4)."},
                           widget=forms.TextInput(attrs={"autocomplete": "shipping postal-code",
                                                         "inputmode": "numeric"}))
    phone = forms.CharField(label="Phone (optional)", max_length=30, required=False,
                            help_text="Only if the carrier needs to reach you about delivery.",
                            widget=forms.TextInput(attrs={"autocomplete": "tel", "type": "tel"}))

    def clean(self):
        data = super().clean()
        if data.get("state") and data.get("zip"):
            problem = ships_to(data["state"], data["zip"])
            if problem:
                self.add_error("zip", problem)
        return data

    def address(self):
        data = self.cleaned_data
        return Address(name=data["name"].strip(), street1=data["street1"].strip(), street2=data["street2"].strip(),
                       city=data["city"].strip(), state=data["state"], zip=data["zip"], phone=data["phone"].strip())

    @classmethod
    def initial_from(cls, email="", address=None):
        initial = {"email": email}
        if address:
            initial.update(address.as_dict())
        return initial


class SubscribeForm(AddressForm):
    consent = forms.BooleanField(
        label="I agree to the automatic renewal terms above, and to being charged at each renewal until I cancel.",
        error_messages={"required": "Tick the box to agree to the renewal terms, or the subscription cannot start."})


class SignInForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=254,
                             widget=forms.EmailInput(attrs={"autocomplete": "email"}))


class DiscountForm(forms.Form):
    code = forms.CharField(label="Discount code", max_length=30)

    def clean_code(self):
        return self.cleaned_data["code"].strip().upper()


def quantity_choices():
    return [(n, str(n)) for n in range(1, settings.CART_MAX_QUANTITY + 1)]
