from django import forms

from .models import Mailing, Subscriber


class SignUpForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=254,
                             widget=forms.EmailInput(attrs={"autocomplete": "email"}))
    frequency = forms.ChoiceField(label="How often, at most", choices=Subscriber.Frequency.choices,
                                  initial=Subscriber.Frequency.MONTHLY, widget=forms.RadioSelect)


class FrequencyForm(forms.Form):
    frequency = forms.ChoiceField(label="How often, at most", choices=Subscriber.Frequency.choices,
                                  widget=forms.RadioSelect)


class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ["subject", "body", "send_until"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 16}),
            "send_until": forms.DateInput(attrs={"type": "date"}),
        }
