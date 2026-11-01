"""Record model changes and logins in the audit log.

Every model is audited unless settings.AUDIT_EXCLUDED_MODELS names it, so a
feature app gets audited without doing anything.  Changes made through the
admin, by agents or by background jobs are all caught here, attributed to
whoever context.current_actor() says is acting.
"""

from django.conf import settings
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import post_delete, post_save, pre_save

from .context import Actor, current_actor
from .recording import MASK, is_sensitive, jsonable, model_label, record

DISPATCH_PREFIX = "apps.audit."


def is_audited(model):
    # Migrations work on historical models (module "__fake__"); their data
    # changes are reviewed code, not someone's action, and may run before
    # the audit table exists.
    if model.__module__ == "__fake__":
        return False
    return model_label(model) not in settings.AUDIT_EXCLUDED_MODELS


def ignored_fields(model):
    rules = settings.AUDIT_IGNORED_FIELDS
    return set(rules.get("*", ())) | set(rules.get(model_label(model), ()))


def field_values(instance):
    """{attname: value} of the instance's concrete fields."""
    return {f.attname: getattr(instance, f.attname) for f in instance._meta.concrete_fields}


def shown(field_name, value):
    return MASK if is_sensitive(field_name) else jsonable(value)


def on_pre_save(sender, instance, raw=False, **kwargs):
    if raw or not is_audited(sender) or instance._state.adding or instance.pk is None:
        return
    attnames = [f.attname for f in sender._meta.concrete_fields]
    instance._audit_old_values = sender._base_manager.filter(pk=instance.pk).values(*attnames).first()


def on_post_save(sender, instance, created, raw=False, **kwargs):
    if raw or not is_audited(sender):
        return
    new = field_values(instance)
    ignored = ignored_fields(sender)
    if created:
        changes = {name: [None, shown(name, value)] for name, value in new.items() if name not in ignored}
        record("create", obj=instance, changes=changes)
        return
    old = getattr(instance, "_audit_old_values", None)
    instance._audit_old_values = None
    if old is None:
        # Saved without an existing row to compare against (e.g. a forced
        # update of a row that pre_save could not read): log the new state.
        changes = {name: [None, shown(name, value)] for name, value in new.items() if name not in ignored}
    else:
        changes = {
            name: [shown(name, old.get(name)), shown(name, value)]
            for name, value in new.items()
            if name not in ignored and old.get(name) != value
        }
        if not changes:
            return
    record("update", obj=instance, changes=changes)


def on_post_delete(sender, instance, **kwargs):
    if not is_audited(sender):
        return
    record("delete", obj=instance)


def _request_actor(request, user=None):
    actor = current_actor()
    if user is not None:
        return Actor(
            type="user",
            user_id=user.pk,
            label=user.get_username(),
            ip_address=actor.ip_address,
            request_path=actor.request_path or getattr(request, "path", ""),
        )
    return actor


def on_logged_in(sender, request, user, **kwargs):
    record("login", obj=user, actor=_request_actor(request, user))


def on_logged_out(sender, request, user, **kwargs):
    if user is None:
        return
    record("logout", obj=user, actor=_request_actor(request, user))


def on_login_failed(sender, credentials, request=None, **kwargs):
    # Django passes credentials with the password already masked.
    username = str(credentials.get("username", ""))
    record("login_failed", message=f"Failed login for username {username!r}", actor=current_actor())


def connect():
    pre_save.connect(on_pre_save, dispatch_uid=DISPATCH_PREFIX + "pre_save")
    post_save.connect(on_post_save, dispatch_uid=DISPATCH_PREFIX + "post_save")
    post_delete.connect(on_post_delete, dispatch_uid=DISPATCH_PREFIX + "post_delete")
    user_logged_in.connect(on_logged_in, dispatch_uid=DISPATCH_PREFIX + "logged_in")
    user_logged_out.connect(on_logged_out, dispatch_uid=DISPATCH_PREFIX + "logged_out")
    user_login_failed.connect(on_login_failed, dispatch_uid=DISPATCH_PREFIX + "login_failed")
