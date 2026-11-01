from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django_otp import user_has_device


def owner_required(view):
    """Allow only staff who signed in with two-factor.

    For back-office pages (owner dashboard, fulfillment, reports):
    - not signed in: to the login page, coming back here afterwards;
    - signed in with password only, no authenticator set up yet (a new
      owner account): to two-factor setup, instead of a login loop;
    - signed in with password only, authenticator set up: to the login
      page to enter the code;
    - signed in with two-factor but not staff (a customer account): 403.
    """

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not user.is_verified():
            if not user_has_device(user, confirmed=True):
                return redirect("two_factor:setup")
            return redirect_to_login(request.get_full_path())
        if not user.is_staff:
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapper
