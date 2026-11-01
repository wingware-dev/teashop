"""Helpers for tests that need a signed-in owner.

Feature apps use these to test pages behind the two-factor login::

    from apps.core.testing import make_owner, login_verified

    owner, device = make_owner()
    login_verified(self.client, owner, device)
"""

from django.contrib.auth import get_user_model
from django_otp import DEVICE_ID_SESSION_KEY
from django_otp.oath import totp
from django_otp.plugins.otp_totp.models import TOTPDevice

OWNER_PASSWORD = "correct-horse-battery-tea"


def make_owner(username="owner", password=OWNER_PASSWORD, staff=True, superuser=True):
    """A user with a confirmed authenticator-app (TOTP) device."""
    user = get_user_model().objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password=password,
        is_staff=staff,
        is_superuser=superuser,
    )
    device = TOTPDevice.objects.create(user=user, name="default", confirmed=True)
    return user, device


def login_verified(client, user, device):
    """Sign the test client in as user, with two-factor already passed."""
    client.force_login(user)
    session = client.session
    session[DEVICE_ID_SESSION_KEY] = device.persistent_id
    session.save()


def current_token(device):
    """The six-digit code the user's authenticator app would show now."""
    code = totp(device.bin_key, device.step, device.t0, device.digits, device.drift)
    return f"{code:0{device.digits}d}"
