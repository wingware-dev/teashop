"""Template helpers for the shop's pages."""

import json
import re

from django import template
from django.templatetags.static import static
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

register = template.Library()

# As django.utils.html.json_script escapes, so the JSON cannot end the
# <script> element or open a comment.
_JSON_ESCAPES = {ord(">"): "\\u003E", ord("<"): "\\u003C", ord("&"): "\\u0026"}


@register.simple_tag
def motif(name, css_class="", label=""):
    """An SVG motif from the sprite.  Decorative (hidden from screen
    readers) unless label is given."""
    href = f"{static('img/motifs.svg')}#motif-{name}"
    if label:
        return format_html(
            '<svg class="motif motif-{} {}" role="img" aria-label="{}" focusable="false"><use href="{}"></use></svg>',
            name, css_class, label, href,
        )
    return format_html(
        '<svg class="motif motif-{} {}" aria-hidden="true" focusable="false"><use href="{}"></use></svg>',
        name, css_class, href,
    )


# Each vine-frame ornament's viewBox in static/img/motifs.svg (#orn-<name>),
# as static/js/vines.js has them: (x, y, width, height).
ORNAMENT_BOXES = {
    "leaf-a": (-1, -9, 32, 18), "leaf-b": (-1, -14, 33, 28), "leaf-c": (-1, -12, 28, 24),
    "blossom": (-14, -14, 28, 28), "berries": (-4, -4, 13, 14), "bird": (-32, -34, 57, 36),
    "butterfly": (-20, -22, 40, 40), "bee": (-12, -15, 29, 21), "dragonfly": (-27, -22, 39, 44),
    "ladybird": (-7, -6, 16, 12), "snail": (-17, -21, 38, 22), "mushroom": (-11, -17, 22, 18),
    "fern": (-12, -18, 24, 37),
}


@register.simple_tag
def ornament(name, x=0, y=0, rotate=0, scale=1, css_class=""):
    """A <use> of a vine-frame ornament, for placing inside an inline
    <svg>: drawn around its origin, moved to (x, y), turned rotate degrees
    and scaled.  css_class "lv1".."lv3" picks a leaf's green."""
    bx, by, bw, bh = ORNAMENT_BOXES[name]
    return format_html(
        '<use href="{}#orn-{}" x="{}" y="{}" width="{}" height="{}" transform="translate({} {}) rotate({}) scale({})" class="{}"></use>',
        static("img/motifs.svg"), name, bx, by, bw, bh, x, y, rotate, scale, css_class,
    )


@register.filter
def money(value):
    """12.5 -> "$12.50"."""
    if value is None or value == "":
        return ""
    return f"${value:,.2f}"


@register.filter
def fahrenheit(celsius):
    return round(celsius * 9 / 5 + 32) if celsius is not None else ""


@register.filter
def ld_json(data):
    """A schema.org JSON-LD <script> element for data."""
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":")).translate(_JSON_ESCAPES)
    return mark_safe(f'<script type="application/ld+json">{text}</script>')


_HEADING = re.compile(r"^##\s+(.+)$")


@register.filter
def article_body(text):
    """Plain text to HTML: blank-line paragraphs, "## " subheadings, line
    breaks kept within a paragraph.  Everything is escaped."""
    blocks = [block.strip() for block in re.split(r"\n\s*\n", (text or "").replace("\r\n", "\n"))]
    parts = []
    for block in blocks:
        if not block:
            continue
        heading = _HEADING.match(block)
        if heading and "\n" not in block:
            parts.append(format_html("<h2>{}</h2>", heading.group(1).strip()))
        else:
            lines = format_html_join(mark_safe("<br>"), "{}", ((line,) for line in block.split("\n")))
            parts.append(format_html("<p>{}</p>", lines))
    return mark_safe("\n".join(parts))


@register.filter
def paragraphs(text):
    """Blank-line paragraphs, escaped (for descriptions and notes)."""
    return article_body(re.sub(r"^##\s+", "", text or "", flags=re.MULTILINE))


@register.inclusion_tag("storefront/_caffeine.html")
def caffeine_meter(product):
    levels = {"none": 0, "low": 1, "medium": 2, "high": 3}
    return {"level": levels.get(product.caffeine), "label": product.get_caffeine_display(), "steps": range(1, 4)}
