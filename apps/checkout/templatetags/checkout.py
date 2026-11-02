"""Template helpers for checkout forms."""

from django import template

register = template.Library()


@register.inclusion_tag("checkout/_field.html")
def field(bound_field):
    """A form field with its label, help text and error, the input tied to
    them for screen readers (aria-describedby, aria-invalid)."""
    described = []
    if bound_field.help_text:
        described.append(f"{bound_field.auto_id}-help")
    if bound_field.errors:
        described.append(f"{bound_field.auto_id}-error")
    attrs = {}
    if described:
        attrs["aria-describedby"] = " ".join(described)
    if bound_field.errors:
        attrs["aria-invalid"] = "true"
    if bound_field.field.required:
        attrs["required"] = True
    return {
        "field": bound_field,
        "widget": bound_field.as_widget(attrs=attrs),
        "is_checkbox": getattr(bound_field.field.widget, "input_type", "") == "checkbox",
    }


@register.filter
def percent(rate):
    """0.08875 -> "8.875%"."""
    if rate is None:
        return ""
    text = f"{rate * 100:.3f}".rstrip("0").rstrip(".")
    return f"{text}%"
