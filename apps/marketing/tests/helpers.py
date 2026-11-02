"""Shared settings and builders for the marketing tests.  Nothing here
calls an AI service or a social network: the agent runs on its stand-in
and the networks' APIs are mocked."""

import io
import shutil
import tempfile
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from PIL import Image

from apps.catalog.models import Product, ProductPhoto
from apps.storefront import demo

MARKETING_SETTINGS = dict(
    STOREFRONT_OPEN=True, SITE_URL="https://shop.example", AGENTS_LIVE=[], MARKETING_POST_LIVE=[],
    BLUESKY_HANDLE="teashop.example", BLUESKY_APP_PASSWORD="app-pass", BLUESKY_SERVICE="https://bsky.example",
    META_PAGE_ID="1234", META_PAGE_TOKEN="page-token", META_INSTAGRAM_ID="5678", META_GRAPH_VERSION="v23.0",
    PINTEREST_TOKEN="pin-token", PINTEREST_BOARD_ID="board-1", MARKETING_POST_AT="09:30",
    MARKETING_POST_GRACE_HOURS=6, MARKETING_WEEKLY_IDEAS=True, JOBS_EAGER=True, ANALYTICS="",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)


def catalog():
    demo.load()
    return Product.objects.get(slug="assam-second-flush")


def jpeg_bytes(size=(600, 400)):
    buffer = io.BytesIO()
    Image.new("RGB", size, (120, 80, 40)).save(buffer, "JPEG")
    return buffer.getvalue()


class TempMedia:
    """A throwaway MEDIA_ROOT for tests that save photos."""

    def __init__(self):
        self.root = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.root)

    def __enter__(self):
        self.override.enable()
        return self

    def __exit__(self, *exc):
        self.override.disable()
        shutil.rmtree(self.root, ignore_errors=True)


def photo(product):
    return ProductPhoto.objects.create(product=product, image=SimpleUploadedFile("tin.jpg", jpeg_bytes()),
                                       alt_text="Dark twisted leaves in an open tin")


def tomorrow():
    return timezone.now() + timedelta(days=1)
