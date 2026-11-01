from apps.core.net import client_ip

from .context import acting_as, actor_for_request


class AuditActorMiddleware:
    """Attribute everything done while handling a request to its user."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        with acting_as(actor_for_request(request, client_ip(request))):
            return self.get_response(request)
