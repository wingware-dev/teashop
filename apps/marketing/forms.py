from django import forms
from django.utils import timezone

from apps.catalog.models import Product, ProductPhoto
from apps.checkout.models import DiscountCode

from . import networks
from .models import Campaign, Idea, Post

LOCAL_FORMAT = "%Y-%m-%dT%H:%M"


class LocalDateTimeInput(forms.DateTimeInput):
    input_type = "datetime-local"

    def __init__(self, **kwargs):
        super().__init__(format=LOCAL_FORMAT, **kwargs)


class DateInput(forms.DateInput):
    input_type = "date"

    def __init__(self, **kwargs):
        super().__init__(format="%Y-%m-%d", **kwargs)


def _products():
    return Product.objects.filter(is_active=True).order_by("name")


class IdeaForm(forms.ModelForm):
    class Meta:
        model = Idea
        fields = ["title", "notes", "product", "campaign"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = _products()
        self.fields["product"].empty_label = "None in particular"
        self.fields["campaign"].empty_label = "None"


class DraftForm(forms.Form):
    """What to ask the assistant for, from an idea."""

    networks = forms.MultipleChoiceField(
        choices=networks.CHOICES, widget=forms.CheckboxSelectMultiple, required=False,
        initial=[name for name, _ in networks.CHOICES])
    campaign = forms.ModelChoiceField(Campaign.objects.all(), required=False, empty_label="The idea's own, if any")
    when = forms.DateTimeField(label="Going out at", widget=LocalDateTimeInput(), input_formats=[LOCAL_FORMAT],
                               help_text="You can change each post's time before approving it")

    def clean_when(self):
        when = self.cleaned_data["when"]
        if when < timezone.now():
            raise forms.ValidationError("Pick a time in the future.")
        return when


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["network", "text", "title", "link", "photo", "gift", "scheduled_for", "campaign", "product"]
        widgets = {"text": forms.Textarea(attrs={"rows": 8}), "scheduled_for": LocalDateTimeInput()}
        labels = {"scheduled_for": "Goes out at", "text": "Text", "product": "About the product"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["scheduled_for"].input_formats = [LOCAL_FORMAT]
        self.fields["scheduled_for"].required = True
        self.fields["photo"].queryset = ProductPhoto.objects.select_related("product").order_by(
            "product__name", "sort_order", "pk")
        self.fields["photo"].empty_label = "No photo"
        self.fields["product"].queryset = _products()
        self.fields["product"].empty_label = "None"
        self.fields["campaign"].empty_label = "None"


class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ["name", "slug", "description", "starts_on", "ends_on", "codes"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3}), "starts_on": DateInput(),
                   "ends_on": DateInput(), "codes": forms.CheckboxSelectMultiple}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["codes"].queryset = DiscountCode.objects.order_by("code")
        self.fields["codes"].required = False


class PublishForm(forms.Form):
    day = forms.DateField(label="Appears in Tea notes from", widget=DateInput(), initial=timezone.localdate)
