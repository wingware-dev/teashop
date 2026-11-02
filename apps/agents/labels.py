"""Saying plainly that an AI wrote it.

California's BOT Act (Bus. & Prof. Code 17940-17943) makes it unlawful to
use a bot to talk with a person online without disclosing it is a bot,
when it is used to sell goods or sway a decision.  The shop discloses
everywhere, whatever the customer's state: every message an agent sends
on its own in chat carries AI_LABEL next to it, and every email an agent
sends on its own starts with email_disclosure().  A reply the owner reads,
edits if needed and sends is the owner's, and carries no label.

Keep the wording clear and up front: not in small print, not only at the
foot.
"""

from django.conf import settings

AI_LABEL = "AI assistant"


def chat_notice():
    """The line shown above a chat the AI assistant answers."""
    return (f"You are chatting with {settings.SHOP_NAME}'s {AI_LABEL}, an AI.  It answers simple questions "
            "(order status, brewing, shipping times) and passes everything else to a person at the shop.")


def email_disclosure():
    """The first lines of an email an agent sends on its own."""
    return (f"[This reply was written by {settings.SHOP_NAME}'s {AI_LABEL}, an AI.  "
            "Reply \"person\" and someone at the shop will answer you.]")


def label_email(body):
    """body with the disclosure at the top."""
    return f"{email_disclosure()}\n\n{body.strip()}\n"


def sender_name(agent_display_name=""):
    """How an agent's messages are signed, e.g. "Teashop AI assistant"."""
    return f"{settings.SHOP_NAME} {AI_LABEL}" + (f" ({agent_display_name})" if agent_display_name else "")
