"""Posting an approved post to its network.

publish(post) -> (external id, URL or "") posts it through the network's
API.  It is used only for networks the owner turned on in
settings.MARKETING_POST_LIVE (with their credentials set: see
check_settings()); every other post is put up by hand by the owner, who
gets it on the dashboard at its time (services.make_due).  Nothing here
runs in tests: they mock requests.

Errors: PostingUnavailable when the network is down or rate-limiting
before anything was posted (the job tries again), PostingError when it
refused the post or the outcome is unknown (a timeout may still have
posted it): the post is marked failed and the owner checks.

The APIs, as documented by each network in November 2026:

- Bluesky (AT Protocol): com.atproto.server.createSession with the
  account's handle and an *app password* (Settings → Privacy and security
  → App passwords), com.atproto.repo.uploadBlob for the photo (at most
  1,000,000 bytes), com.atproto.repo.createRecord for the post, with
  link facets so the link is clickable.
- Facebook Page and Instagram (Meta Graph API): a Page access token with
  pages_manage_posts and instagram_content_publish.  Facebook: POST
  /{page-id}/photos (with a photo) or /{page-id}/feed.  Instagram: POST
  /{ig-user-id}/media with a public JPEG URL, then /media_publish.
- Pinterest (API v5): POST /v5/pins with a board id and the photo's URL,
  using an access token with pins:write and boards:read.
"""

import io
import logging
import re

import requests
from django.conf import settings
from django.core import checks
from django.utils import timezone

from . import networks

log = logging.getLogger(__name__)

TIMEOUT = 30
LIVE_NETWORKS = ("bluesky", "facebook", "instagram", "pinterest")
CREDENTIALS = {
    "bluesky": ("BLUESKY_HANDLE", "BLUESKY_APP_PASSWORD"),
    "facebook": ("META_PAGE_ID", "META_PAGE_TOKEN"),
    "instagram": ("META_INSTAGRAM_ID", "META_PAGE_TOKEN"),
    "pinterest": ("PINTEREST_TOKEN", "PINTEREST_BOARD_ID"),
}
BLUESKY_MAX_IMAGE = 1_000_000
RETRY_STATUSES = {429, 500, 502, 503, 504}


class PostingError(Exception):
    """The network refused the post, or it is unknown whether it went."""


class PostingUnavailable(PostingError):
    """The network is down or busy and nothing was posted: try later."""


def posts_live(network):
    return network in settings.MARKETING_POST_LIVE and network in LIVE_NETWORKS


@checks.register()
def check_settings(app_configs=None, **kwargs):
    """Startup check: MARKETING_POST_LIVE names only networks we can post
    to, each with its credentials."""
    errors = []
    for network in settings.MARKETING_POST_LIVE:
        if network not in LIVE_NETWORKS:
            why = networks.NETWORKS[network].why_by_hand if network in networks.NETWORKS else "No such network."
            errors.append(checks.Error(f"MARKETING_POST_LIVE names {network!r}, which is posted by hand: {why}",
                                       hint="Use bluesky, facebook, instagram or pinterest.", id="marketing.E001"))
            continue
        missing = [name for name in CREDENTIALS[network] if not getattr(settings, name, "")]
        if missing:
            errors.append(checks.Error(f"MARKETING_POST_LIVE names {network!r} but {', '.join(missing)} is not set",
                                       hint="See docs/marketing.md, \"Posting\".", id="marketing.E002"))
    return errors


def _absolute(path):
    return settings.SITE_URL.rstrip("/") + path


def photo_url(post):
    """The photo's public URL (the cleaned JPEG original, which Instagram
    and Pinterest fetch themselves)."""
    return _absolute(post.photo.image.url) if post.photo_id else ""


def _check(response, network):
    if response.status_code in RETRY_STATUSES:
        raise PostingUnavailable(f"{network} is busy or failing (HTTP {response.status_code}); nothing was posted")
    if response.status_code >= 400:
        raise PostingError(f"{network} refused the post (HTTP {response.status_code}): {response.text[:300]}")
    try:
        return response.json()
    except ValueError as exc:
        raise PostingError(f"{network} answered with something other than JSON: {response.text[:200]}") from exc


def _post(url, network, *, first=False, **kwargs):
    """requests.post with the errors sorted: a call that couldn't connect
    posted nothing; a timeout on the call that posts may have."""
    try:
        return _check(requests.post(url, timeout=TIMEOUT, **kwargs), network)
    except requests.ConnectionError as exc:
        raise PostingUnavailable(f"Couldn't reach {network}: {exc}") from exc
    except requests.Timeout as exc:
        if first:
            raise PostingUnavailable(f"{network} didn't answer: {exc}") from exc
        raise PostingError(f"{network} didn't answer in time; check whether the post went up before trying again") \
            from exc


# -- Bluesky ------------------------------------------------------------------------

def _bluesky_image(post):
    """The photo as JPEG bytes under Bluesky's size limit."""
    from PIL import Image

    with post.photo.image.open("rb") as file, Image.open(file) as original:
        original.load()
        image = original.convert("RGB")
    for side, quality in ((2000, 85), (1600, 80), (1200, 75), (1000, 70), (800, 65)):
        copy = image.copy()
        copy.thumbnail((side, side), Image.LANCZOS)
        buffer = io.BytesIO()
        copy.save(buffer, "JPEG", quality=quality, optimize=True)
        if buffer.tell() <= BLUESKY_MAX_IMAGE:
            return buffer.getvalue()
    raise PostingError("The photo is too large for Bluesky even when made smaller")


def link_facets(text):
    """Bluesky's link facets (byte offsets in UTF-8) for each URL in text."""
    facets = []
    for match in networks.URL_RE.finditer(text):
        url = match.group(0).rstrip(".,;:!?)")
        start = len(text[:match.start()].encode())
        facets.append({"index": {"byteStart": start, "byteEnd": start + len(url.encode())},
                       "features": [{"$type": "app.bsky.richtext.facet#link", "uri": url}]})
    return facets


def publish_bluesky(post):
    service = settings.BLUESKY_SERVICE.rstrip("/")
    session = _post(f"{service}/xrpc/com.atproto.server.createSession", "Bluesky", first=True,
                    json={"identifier": settings.BLUESKY_HANDLE, "password": settings.BLUESKY_APP_PASSWORD})
    auth = {"Authorization": f"Bearer {session['accessJwt']}"}
    text = post.final_text()
    record = {"$type": "app.bsky.feed.post", "text": text, "createdAt": timezone.now().isoformat(),
              "langs": ["en"]}
    facets = link_facets(text)
    if facets:
        record["facets"] = facets
    if post.photo_id:
        blob = _post(f"{service}/xrpc/com.atproto.repo.uploadBlob", "Bluesky", first=True,
                     headers={**auth, "Content-Type": "image/jpeg"}, data=_bluesky_image(post))
        record["embed"] = {"$type": "app.bsky.embed.images",
                           "images": [{"alt": post.photo.alt_text, "image": blob["blob"]}]}
    created = _post(f"{service}/xrpc/com.atproto.repo.createRecord", "Bluesky", headers=auth,
                    json={"repo": session["did"], "collection": "app.bsky.feed.post", "record": record})
    uri = created.get("uri", "")
    rkey = uri.rsplit("/", 1)[-1] if uri else ""
    handle = session.get("handle") or settings.BLUESKY_HANDLE
    return uri, f"https://bsky.app/profile/{handle}/post/{rkey}" if rkey else ""


# -- Meta: Facebook Page and Instagram ------------------------------------------------

def _graph(path):
    return f"https://graph.facebook.com/{settings.META_GRAPH_VERSION}/{path}"


def publish_facebook(post):
    token = settings.META_PAGE_TOKEN
    page = settings.META_PAGE_ID
    link = post.tracked_link()
    if post.photo_id:
        caption = post.text if not link else f"{post.text.rstrip()}\n{link}"
        result = _post(_graph(f"{page}/photos"), "Facebook", data={"url": photo_url(post), "caption": caption,
                                                                     "access_token": token})
        post_id = result.get("post_id") or result.get("id", "")
    else:
        data = {"message": post.text, "access_token": token}
        if link:
            data["link"] = link
        result = _post(_graph(f"{page}/feed"), "Facebook", data=data)
        post_id = result.get("id", "")
    return post_id, f"https://www.facebook.com/{post_id}" if post_id else ""


def publish_instagram(post):
    token = settings.META_PAGE_TOKEN
    user = settings.META_INSTAGRAM_ID
    container = _post(_graph(f"{user}/media"), "Instagram", first=True,
                      data={"image_url": photo_url(post), "caption": post.text, "alt_text": post.photo.alt_text,
                            "access_token": token})
    published = _post(_graph(f"{user}/media_publish"), "Instagram",
                      data={"creation_id": container["id"], "access_token": token})
    return published.get("id", ""), ""


# -- Pinterest -------------------------------------------------------------------------

def publish_pinterest(post):
    body = {"board_id": settings.PINTEREST_BOARD_ID, "title": post.title[:100], "description": post.text[:500],
            "alt_text": post.photo.alt_text[:500],
            "media_source": {"source_type": "image_url", "url": photo_url(post)}}
    if post.link:
        body["link"] = post.tracked_link()
    result = _post("https://api.pinterest.com/v5/pins", "Pinterest", json=body,
                   headers={"Authorization": f"Bearer {settings.PINTEREST_TOKEN}"})
    pin = result.get("id", "")
    return pin, f"https://www.pinterest.com/pin/{pin}/" if pin else ""


PUBLISHERS = {
    "bluesky": publish_bluesky,
    "facebook": publish_facebook,
    "instagram": publish_instagram,
    "pinterest": publish_pinterest,
}


def publish(post):
    """Post it now through its network's API: (external id, URL)."""
    if not posts_live(post.network):
        raise PostingError(f"{post.get_network_display()} is posted by hand")
    if networks.get(post.network).needs_image and not post.photo_id:
        raise PostingError(f"{post.get_network_display()} needs a photo")
    external_id, url = PUBLISHERS[post.network](post)
    return str(external_id)[:300], re.sub(r"\s", "", url)[:500]
