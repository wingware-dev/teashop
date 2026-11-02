from django import forms

from .services import MAX_MESSAGE_CHARS

MESSAGE_ATTRS = {"rows": 4, "maxlength": MAX_MESSAGE_CHARS}


class StartChatForm(forms.Form):
    email = forms.EmailField(label="Your email", help_text="So we can reply if you leave this page.",
                             widget=forms.EmailInput(attrs={"autocomplete": "email"}))
    name = forms.CharField(label="Your name (optional)", required=False, max_length=100,
                           widget=forms.TextInput(attrs={"autocomplete": "name"}))
    message = forms.CharField(label="Your question", max_length=MAX_MESSAGE_CHARS,
                              widget=forms.Textarea(attrs=MESSAGE_ATTRS))


class ChatMessageForm(forms.Form):
    message = forms.CharField(label="Your message", max_length=MAX_MESSAGE_CHARS,
                              widget=forms.Textarea(attrs={**MESSAGE_ATTRS, "rows": 3}))


class OwnerReplyForm(forms.Form):
    body = forms.CharField(label="Reply", max_length=MAX_MESSAGE_CHARS,
                           widget=forms.Textarea(attrs={**MESSAGE_ATTRS, "rows": 8}))
    draft = forms.IntegerField(required=False, widget=forms.HiddenInput)
