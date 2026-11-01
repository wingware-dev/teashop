from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.db.utils import DatabaseError
from django.test import TestCase
from django.urls import reverse

from apps.audit import Actor, acting_as, acting_as_agent, current_actor, record
from apps.audit.models import AppendOnlyError, AuditEvent
from apps.core.testing import OWNER_PASSWORD, current_token, login_verified, make_owner

User = get_user_model()


def events(action=None, object_type="auth.user"):
    qs = AuditEvent.objects.filter(object_type=object_type).order_by("id")
    return qs.filter(action=action) if action else qs


class ModelChangeTests(TestCase):
    def test_create_update_delete_are_recorded(self):
        with acting_as(Actor(type="user", user_id=99, label="owner", ip_address="203.0.113.5")):
            user = User.objects.create_user("clerk", password="a-long-password-123")
            user.first_name = "Pat"
            user.save()
            user_id = user.pk
            user.delete()

        create, update, delete = events()
        self.assertEqual([e.action for e in (create, update, delete)], ["create", "update", "delete"])
        for event in (create, update, delete):
            self.assertEqual(event.actor_type, "user")
            self.assertEqual(event.actor_user_id, 99)
            self.assertEqual(event.actor_label, "owner")
            self.assertEqual(event.ip_address, "203.0.113.5")
            self.assertEqual(event.object_id, str(user_id))
        self.assertEqual(update.changes, {"first_name": ["", "Pat"]})
        self.assertEqual(delete.object_repr, "clerk")

    def test_passwords_and_keys_are_masked(self):
        user = User.objects.create_user("clerk", password="a-long-password-123")
        self.assertEqual(events("create")[0].changes["password"], [None, "***"])
        user.set_password("another-long-password-456")
        user.save()
        self.assertEqual(events("update")[0].changes, {"password": ["***", "***"]})

        owner, device = make_owner(username="keyholder")
        device_event = AuditEvent.objects.get(object_type="otp_totp.totpdevice", action="create")
        self.assertEqual(device_event.changes["key"], [None, "***"])
        self.assertNotIn(device.key, str(device_event.changes))

    def test_unchanged_save_and_ignored_fields_make_no_event(self):
        user = User.objects.create_user("clerk", password="a-long-password-123")
        user.save()
        from django.utils import timezone

        user.last_login = timezone.now()
        user.save()
        self.assertEqual(events("update").count(), 0)

    def test_excluded_models_are_not_recorded(self):
        record("ops.note", message="hello")
        self.assertFalse(AuditEvent.objects.filter(object_type="audit.auditevent").exists())

    def test_without_context_actor_is_system(self):
        User.objects.create_user("clerk")
        event = events("create")[0]
        self.assertEqual(event.actor_type, "system")
        self.assertEqual(event.actor_label, "system")


class AgentAndManualRecordTests(TestCase):
    def test_agent_actions_are_attributed_to_agent(self):
        with acting_as_agent("support-agent"):
            self.assertEqual(current_actor().type, "agent")
            target = User.objects.create_user("customer")
            record("support.reply_sent", obj=target, message="Answered order-status question")
        self.assertEqual(current_actor().type, "system")  # context restored

        sent = AuditEvent.objects.get(action="support.reply_sent")
        self.assertEqual((sent.actor_type, sent.actor_label), ("agent", "support-agent"))
        self.assertEqual((sent.object_type, sent.object_repr), ("auth.user", "customer"))
        self.assertEqual(events("create")[0].actor_label, "support-agent")

    def test_agent_needs_a_name(self):
        with self.assertRaises(ValueError):
            acting_as_agent("")


class AppendOnlyTests(TestCase):
    def test_model_refuses_update_and_delete(self):
        event = record("ops.note")
        event.message = "rewritten"
        with self.assertRaises(AppendOnlyError):
            event.save()
        with self.assertRaises(AppendOnlyError):
            event.delete()

    @skipUnless(connection.vendor == "postgresql", "trigger exists on PostgreSQL only")
    def test_database_refuses_raw_update_and_delete(self):
        event = record("ops.note")
        for sql in ("UPDATE audit_auditevent SET message = 'x' WHERE id = %s",
                    "DELETE FROM audit_auditevent WHERE id = %s"):
            with self.subTest(sql=sql):
                with self.assertRaisesMessage(DatabaseError, "append-only"):
                    with transaction.atomic(), connection.cursor() as cursor:
                        cursor.execute(sql, [event.pk])


class RequestAttributionTests(TestCase):
    def test_login_logout_and_failed_login_are_recorded(self):
        owner, device = make_owner()
        login = reverse("two_factor:login")
        self.client.post(login, {"login_view-current_step": "auth", "auth-username": "owner",
                                 "auth-password": "wrong"}, REMOTE_ADDR="198.51.100.7")
        failed = AuditEvent.objects.get(action="login_failed")
        self.assertIn("'owner'", failed.message)
        self.assertEqual(failed.ip_address, "198.51.100.7")
        self.assertNotIn("wrong", failed.message)

        self.client.post(login, {"login_view-current_step": "auth", "auth-username": "owner",
                                 "auth-password": OWNER_PASSWORD})
        self.client.post(login, {"login_view-current_step": "token",
                                 "token-otp_token": current_token(device)})
        logged_in = AuditEvent.objects.get(action="login")
        self.assertEqual((logged_in.actor_type, logged_in.actor_label), ("user", "owner"))

        self.client.post(reverse("core:logout"))
        self.assertTrue(AuditEvent.objects.filter(action="logout", actor_label="owner").exists())

    def test_admin_change_is_attributed_to_signed_in_owner(self):
        owner, device = make_owner()
        login_verified(self.client, owner, device)
        clerk = User.objects.create_user("clerk")
        url = reverse("admin:auth_user_change", args=[clerk.pk])
        page = self.client.get(url)
        form = page.context["adminform"].form
        data = {name: value for name, value in form.initial.items() if value is not None and name != "password"}
        data.update({"username": "clerk", "first_name": "Robin", "date_joined_0": "2026-01-01",
                     "date_joined_1": "00:00:00", "groups": [], "user_permissions": []})
        response = self.client.post(url, data, REMOTE_ADDR="203.0.113.20")
        self.assertEqual(response.status_code, 302, getattr(response, "context", None)
                         and response.context["adminform"].form.errors)

        update = events("update").get(object_id=str(clerk.pk))
        self.assertEqual(update.changes["first_name"], ["", "Robin"])
        self.assertEqual((update.actor_type, update.actor_label, update.actor_user_id),
                         ("user", "owner", owner.pk))
        self.assertEqual(update.ip_address, "203.0.113.20")
        self.assertEqual(update.request_path, url)

    def test_audit_log_is_read_only_in_admin(self):
        owner, device = make_owner()
        login_verified(self.client, owner, device)
        event = record("ops.note")
        self.assertEqual(self.client.get(reverse("admin:audit_auditevent_changelist")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:audit_auditevent_add")).status_code, 403)
        self.assertEqual(self.client.post(reverse("admin:audit_auditevent_delete", args=[event.pk])).status_code, 403)
