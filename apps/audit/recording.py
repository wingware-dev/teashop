from .context import current_actor

# Field names containing any of these have their values masked in the log.
SENSITIVE_FIELD_PARTS = ("password", "secret", "token", "key")
MASK = "***"


def is_sensitive(field_name):
    name = field_name.lower()
    return any(part in name for part in SENSITIVE_FIELD_PARTS)


def jsonable(value):
    """A value the audit log can store as JSON."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def model_label(model):
    return model._meta.label_lower


def record(action, *, obj=None, changes=None, message="", actor=None,
           object_type="", object_id="", object_repr=""):
    """Write one audit event and return it.

    action: a short verb ("create", "login") or a dotted name for a
    feature's own actions ("fulfillment.label_purchased").
    obj: the model instance acted on, if any; or give object_type,
    object_id and object_repr directly.
    actor: defaults to whoever is acting in the current context.
    """
    from .models import AuditEvent  # not at import time: apps.audit is imported before models load

    actor = actor or current_actor()
    if obj is not None:
        # obj._meta, not type(obj): request.user is a lazy proxy object.
        object_type = object_type or model_label(obj)
        object_id = object_id or ("" if obj.pk is None else str(obj.pk))
        object_repr = object_repr or str(obj)
    return AuditEvent.objects.create(
        actor_type=actor.type,
        actor_user_id=actor.user_id,
        actor_label=actor.label[:150],
        action=action[:64],
        object_type=object_type[:100],
        object_id=str(object_id)[:64],
        object_repr=str(object_repr)[:200],
        changes=changes or {},
        message=message,
        ip_address=actor.ip_address,
        request_path=actor.request_path[:300],
    )
