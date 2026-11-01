from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils import timezone


class AppendOnlyError(Exception):
    """Raised on an attempt to change or delete a recorded audit event."""


class AuditEvent(models.Model):
    """One recorded action.  Rows are never changed or deleted by the app;
    on PostgreSQL a trigger enforces this in the database too."""

    class ActorType(models.TextChoices):
        USER = "user", "User"
        AGENT = "agent", "AI agent"
        SYSTEM = "system", "System"
        ANONYMOUS = "anonymous", "Anonymous visitor"

    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    actor_type = models.CharField(max_length=16, choices=ActorType.choices)
    # A plain id, not a foreign key, so deleting a user never touches the log.
    actor_user_id = models.BigIntegerField(null=True, blank=True)
    actor_label = models.CharField(max_length=150, blank=True, help_text="Username or agent name at the time")
    action = models.CharField(max_length=64, db_index=True)
    object_type = models.CharField(max_length=100, blank=True, help_text="app_label.model")
    object_id = models.CharField(max_length=64, blank=True)
    object_repr = models.CharField(max_length=200, blank=True)
    changes = models.JSONField(default=dict, blank=True, encoder=DjangoJSONEncoder)
    message = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    request_path = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["-timestamp", "-id"]
        indexes = [models.Index(fields=["object_type", "object_id"])]

    def __str__(self):
        target = f" {self.object_type}#{self.object_id}" if self.object_type else ""
        return f"{self.timestamp:%Y-%m-%d %H:%M:%S} {self.actor_label or self.actor_type} {self.action}{target}"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise AppendOnlyError("Audit events cannot be changed")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise AppendOnlyError("Audit events cannot be deleted")
