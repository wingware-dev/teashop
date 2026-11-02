"""Who is acting right now, for attributing audit events.

The actor lives in a context variable, so it follows the current request or
job without being passed around.  AuditActorMiddleware sets it per request;
background jobs and agents set it with acting_as() / acting_as_agent().
"""

import contextvars
from contextlib import contextmanager
from dataclasses import dataclass


@dataclass(frozen=True)
class Actor:
    type: str  # one of AuditEvent.ActorType's values
    user_id: int | None = None
    label: str = ""
    ip_address: str | None = None
    request_path: str = ""


SYSTEM = Actor(type="system", label="system")

_current = contextvars.ContextVar("audit_actor", default=None)


def current_actor():
    return _current.get() or SYSTEM


@contextmanager
def acting_as(actor):
    token = _current.set(actor)
    try:
        yield actor
    finally:
        _current.reset(token)


def acting_as_agent(name):
    """Attribute what is done inside the block to the named AI agent: the
    changes its tools make, and the messages and drafts it sends.  Not
    what the shop does on the side: jobs queued in the block run as the
    system (apps.jobs), and lazily created settings singletons are made
    with acting_as_system()."""
    if not name:
        raise ValueError("An agent needs a name for the audit log")
    return acting_as(Actor(type="agent", label=name))


def acting_as_system():
    """Attribute what is done inside the block to the system, whoever is
    acting around it: for housekeeping nobody decided on, such as creating
    a settings row the first time it is read."""
    return acting_as(SYSTEM)


def actor_for_request(request, ip_address):
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        return Actor(
            type="user",
            user_id=user.pk,
            label=user.get_username(),
            ip_address=ip_address,
            request_path=request.path,
        )
    return Actor(type="anonymous", label="anonymous", ip_address=ip_address, request_path=request.path)
