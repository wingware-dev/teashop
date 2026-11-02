"""Product photos: clean each upload, and make the smaller copies that
phones load.

- clean_upload() turns the photo upright (phones store rotation as a tag),
  drops every bit of metadata, location above all, and limits it to
  MAX_SIDE pixels, re-saving it as JPEG.
- make_renditions() saves WebP copies RENDITION_WIDTHS wide next to it
  (``<name>-<width>.webp``), so pages can offer a srcset and phones load
  a 480-pixel image rather than the 2000-pixel one.
"""

import io
import logging
import posixpath

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

log = logging.getLogger(__name__)

MAX_SIDE = 2000
RENDITION_WIDTHS = (480, 960, 1440)
JPEG_QUALITY = 85
WEBP_QUALITY = 80


def clean_upload(photo):
    """Replace photo.image's pending upload with an upright, metadata-free
    JPEG at most MAX_SIDE pixels on its longer side."""
    upload = photo.image
    try:
        upload.seek(0)
        with Image.open(upload) as original:
            original.load()
            image = ImageOps.exif_transpose(original)
    except (UnidentifiedImageError, OSError) as exc:
        raise ValidationError({"image": "This file is not a photo the site can read; upload a JPEG, PNG or WebP."}) from exc
    image = image.convert("RGB")
    image.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
    buffer = io.BytesIO()
    # A fresh image object carries no EXIF, XMP or ICC data unless asked.
    image.save(buffer, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
    base = posixpath.splitext(posixpath.basename(upload.name))[0] or "photo"
    photo.image.save(f"{base}.jpg", ContentFile(buffer.getvalue()), save=False)
    # Saving the file this way leaves the dimension fields empty.
    photo.width, photo.height = image.size


def rendition_name(photo, width):
    return f"{posixpath.splitext(photo.image.name)[0]}-{width}.webp"


def widths_for(photo):
    """The rendition widths smaller than the photo itself."""
    return [width for width in RENDITION_WIDTHS if width < photo.width]


def make_renditions(photo):
    """Save the WebP copies that are missing."""
    if not photo.image:
        return
    storage = photo.image.storage
    needed = [width for width in widths_for(photo) if not storage.exists(rendition_name(photo, width))]
    if not needed:
        return
    with photo.image.open("rb") as file, Image.open(file) as original:
        original.load()
        image = original.convert("RGB")
    for width in needed:
        copy = image.copy()
        copy.thumbnail((width, width * 10), Image.LANCZOS)
        buffer = io.BytesIO()
        copy.save(buffer, "WEBP", quality=WEBP_QUALITY, method=5)
        storage.save(rendition_name(photo, width), ContentFile(buffer.getvalue()))


def delete_renditions(photo):
    if not photo.image:
        return
    for width in RENDITION_WIDTHS:
        name = rendition_name(photo, width)
        if photo.image.storage.exists(name):
            photo.image.storage.delete(name)


def rendition_url(photo, width):
    """The URL of the smallest copy at least width wide, else the photo."""
    for candidate in widths_for(photo):
        if candidate >= width:
            return photo.image.storage.url(rendition_name(photo, candidate))
    return photo.image.url


def srcset(photo):
    """'url 480w, url 960w, ..., original <width>w' for <img srcset>."""
    entries = [f"{photo.image.storage.url(rendition_name(photo, w))} {w}w" for w in widths_for(photo)]
    entries.append(f"{photo.image.url} {photo.width}w")
    return ", ".join(entries)
