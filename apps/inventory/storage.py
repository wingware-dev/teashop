"""Private file storage for supplier documents (spec sheets, allergen
statements, certificates, packing slips).

Files go under settings.PRIVATE_MEDIA_ROOT, which Caddy does not serve;
the owner downloads them through inventory:private_file, behind the
two-factor login.
"""

import os
import uuid

from django.conf import settings
from django.core.files.storage import FileSystemStorage, storages
from django.utils.functional import cached_property
from django.core.validators import FileExtensionValidator
from django.urls import reverse
from django.utils import timezone

DOCUMENT_EXTENSIONS = ["pdf", "png", "jpg", "jpeg", "webp", "txt", "csv", "xlsx", "docx"]

validate_document_extension = FileExtensionValidator(allowed_extensions=DOCUMENT_EXTENSIONS)


class PrivateFileStorage(FileSystemStorage):
    """Files outside the public media directory, whose URLs point at the
    owner-only download view.  Without a location option it follows
    settings.PRIVATE_MEDIA_ROOT, as FileSystemStorage follows MEDIA_ROOT
    (tests can override it)."""

    @cached_property
    def base_location(self):
        return self._value_or_setting(self._location, settings.PRIVATE_MEDIA_ROOT)

    def _clear_cached_properties(self, setting, **kwargs):
        super()._clear_cached_properties(setting, **kwargs)
        if setting == "PRIVATE_MEDIA_ROOT":
            self.__dict__.pop("base_location", None)
            self.__dict__.pop("location", None)

    def url(self, name):
        return reverse("inventory:private_file", args=[name.replace("\\", "/")])


def private_storage():
    return storages["private"]


def document_path(instance, filename):
    """inventory/2026/11/<random>-<original name>, so names never collide
    and cannot be guessed from the lot."""
    base = os.path.basename(filename)
    return f"inventory/{timezone.now():%Y/%m}/{uuid.uuid4().hex[:12]}-{base}"
