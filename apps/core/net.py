import ipaddress

from django.conf import settings


def _valid_ip(value):
    try:
        return str(ipaddress.ip_address(value.strip()))
    except ValueError:
        return None


def client_ip(request):
    """The visitor's IP address, or None if it can't be told.

    Behind Caddy (settings.TRUST_X_REAL_IP on) the address is the X-Real-IP
    header, which Caddy overwrites on every request so visitors cannot forge
    it.  Otherwise it is the TCP peer address.  X-Forwarded-For is never
    used: its first entries come from the visitor and can be faked.
    """
    if settings.TRUST_X_REAL_IP:
        forwarded = _valid_ip(request.META.get("HTTP_X_REAL_IP", ""))
        if forwarded:
            return forwarded
    return _valid_ip(request.META.get("REMOTE_ADDR", ""))
