"""{% analytics_script %}: the privacy-respecting analytics script
(Plausible or self-hosted Umami, settings.ANALYTICS), on the shop's
catalog pages only.

Neither sets cookies or keeps personal data, so no cookie banner is
needed.  It is left off every page whose address could hold something
private or isn't the public shop: checkout, orders, accounts, sign-in
links, the chat, the email list's links and all owner pages.  Campaign
links carry utm_* words, which both tools report by campaign.
"""

from django import template
from django.conf import settings
from django.utils.html import format_html

register = template.Library()


def tracked(request):
    match = getattr(request, "resolver_match", None)
    if match is None or match.namespace != "storefront":
        return False
    return not match.url_name.startswith("variant_") and not request.path.startswith("/owner/")


@register.simple_tag(takes_context=True)
def analytics_script(context):
    request = context.get("request")
    if not settings.ANALYTICS or request is None or not tracked(request):
        return ""
    if settings.ANALYTICS == "plausible":
        return format_html('<script defer data-domain="{}" src="{}"></script>', settings.ANALYTICS_SITE_ID,
                           settings.ANALYTICS_SCRIPT_URL)
    return format_html('<script defer data-website-id="{}" data-do-not-track="true" src="{}"></script>',
                       settings.ANALYTICS_SITE_ID, settings.ANALYTICS_SCRIPT_URL)
