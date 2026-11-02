"""Checkout's periodic jobs (apps.jobs imports this at startup; see
docs/jobs.md).  The emails' own jobs are in emails.py."""

from apps import jobs


@jobs.job
def subscription_reminders():
    """Queue the renewal reminders due for yearly subscriptions (NY GBL
    527-a, California's automatic renewal law)."""
    from . import subscriptions

    subscriptions.send_reminders()


jobs.schedule(subscription_reminders, daily_at="14:00", tz="UTC")


@jobs.job(max_attempts=6)
def record_payment_fee(order_id):
    """Keep Stripe's fee on the order's payment, for the profit reports
    and the daily accounting summary.  Stripe settles the fee a little
    after the payment, so a fee not known yet is asked for again later."""
    from datetime import timedelta

    from . import payments
    from .models import Order

    order = Order.objects.filter(pk=order_id).first()
    if order is None or order.payment_fee is not None or order.payment_provider != "stripe":
        return
    provider = payments.provider()
    if provider.name != "stripe":
        return
    fee = provider.payment_fee(order)
    if fee is None:
        raise jobs.Retry("Stripe has not settled the fee yet", delay=timedelta(minutes=30))
    order.payment_fee = fee
    order.save(update_fields=["payment_fee"])
