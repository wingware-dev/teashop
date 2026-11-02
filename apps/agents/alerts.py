"""AI spending on the owner dashboard's "Needs your attention" queue: near
the monthly cap, and at it (when agents hand everything to the owner)."""

from django.urls import reverse

from apps.core.attention import Attention

from . import budget


def attention_items():
    spent, cap = budget.spent_this_month(), budget.cap()
    month = budget.month_start().strftime("%Y-%m")
    url = reverse("agents:owner_home")
    if cap <= 0 or spent >= cap:
        return [Attention(
            f"AI spending cap reached: ${spent:.2f} of ${cap:.2f}",
            "The agents make no more AI calls this month: support hands every question to you.  Raise "
            "AGENTS_MONTHLY_CAP in .env and redeploy, or wait for the new month.", url, "urgent",
            kind="problems", key=f"agents:cap-reached:{month}")]
    if spent >= cap * budget.WARN_AT:
        return [Attention(
            f"AI spending at ${spent:.2f} of the ${cap:.2f} monthly cap",
            "When it is reached, the agents stop calling the AI and hand their work to you.", url, "warning",
            kind="other", key=f"agents:cap-near:{month}")]
    return []
