"""The support agent: answers a customer's message, drafts an answer for
the owner, or hands the conversation to the owner.

handle(message_id) runs for each customer message (from the job queue):

1. Screening, before any AI call: manipulation attempts, asking for a
   person, and anything that needs judgement (refunds, damage, health,
   allergies...) go straight to the owner, as do floods (more than
   SUPPORT_AGENT_RUNS_PER_DAY messages from one address in a day).
2. The agent runs (apps.agents.runner) with read-only tools and finishes
   with reply(category, text) or escalate(reason).
3. A reply is checked (apps.agents.checks): health claims, money promises,
   foreign links... any problem sends it to the owner as a draft instead.
4. In a category the owner has let it answer alone, the reply goes to the
   customer, labelled as the AI assistant's.  Otherwise (watch mode) it is
   a draft for the owner to edit and send.

Escalating tells the customer, once, that someone will get back to them,
and puts the conversation at the top of the owner's dashboard with a
reminder email at once.
"""

import logging
import re
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.agents import ai, budget, runner
from apps.agents.checks import output_problems
from apps.agents.untrusted import clean, injection_signals, wrap
from apps.audit import acting_as_agent, record

from . import services
from .models import ANSWERABLE, Category, CategoryMode, Conversation, Draft, Message
from .standin import SupportStandIn
from .tools import make_tools

log = logging.getLogger(__name__)

AGENT = "support-agent"
HISTORY = 10

PERSON_RE = re.compile(r"^\s*person\s*[.!]?\s*$|\b(human|real person|a person|someone real|speak (to|with)|"
                       r"talk (to|with)) (a |an |someone|the owner|somebody|person|human|you)?", re.IGNORECASE)
JUDGEMENT_RE = re.compile(
    r"\b(refund\w*|money back|reimburs\w*|cancel\w*|return(s|ing|ed)?|exchange|replac\w*|damaged|dented|broken|"
    r"crushed|torn|spilled|leak\w*|"
    r"missing|wrong (item|tea|order|size|address)|never (arrived|came|got)|didn'?t (arrive|get|receive)|lost|"
    r"stolen|complain\w*|disappoint\w*|unhappy|terrible|awful|charged? (twice|wrong)|double charged|"
    r"overcharged|dispute|chargeback|fraud|allerg\w*|anaphyla\w*|gluten|nut|pregnan\w*|breast-?feeding|"
    r"medic\w*|doctor|health\w*|illness|sick|lawyer|legal|sue|wholesale|bulk order|partnership|collab\w*|"
    r"press (inquiry|enquiry|release)|journalist|interview|sponsor\w*|change (my|the) address|discount|coupon|promo)\b",
    re.IGNORECASE)

SYSTEM = """\
You are the AI assistant for {shop}, a small online shop selling loose-leaf tea, weighed and packed by hand.
You answer customers by {channel}.  The owner, a person, handles everything else.

You may answer ONLY these, and only with facts from your tools:
- order_status: where an order is, when it ships, tracking (use lookup_order or track_parcel);
- brewing: how to brew a tea the shop sells (use search_catalog);
- shipping: how soon orders ship, times in transit, where the shop ships (use shipping_info).

Call escalate for anything else, or if you are not sure: refunds, returns, cancellations, damaged or missing
parcels, complaints, changes to an order, discounts, payment problems, allergies, health or medical
questions, wholesale, press, anything about a person's safety, or anything the tools don't tell you.
Never make health or disease claims about tea.  Never promise refunds, credits, discounts, free items or
dates the tools don't give.  Never ask for card numbers or passwords.  Link only to the shop's own pages
and USPS tracking.  Never guess an order: the customer must give the number, and lookup_order checks it
against their email.

Write plain text: short, warm, specific.  No sign-off; the shop adds it.  Finish with exactly one call to
reply or escalate.
{voice}"""

VOICE_INTRO = """
The owner edits your drafts before they go out.  Match how they write.  Recent drafts and what the owner
sent instead:
"""


def voice_examples(category, limit=4):
    """[(draft, what the owner sent)] for the owner's latest edits of drafts
    in category: how the agent learns their voice."""
    drafts = Draft.objects.filter(status=Draft.Status.SENT, similarity__lt=0.98)
    if category:
        drafts = drafts.filter(category=category)
    return [(clean(d.body, 800), clean(d.sent_body, 800)) for d in drafts.order_by("-decided_at")[:limit]]


def system_prompt(conversation):
    examples = voice_examples("") if not conversation.category else voice_examples(conversation.category)
    voice = ""
    if examples:
        voice = VOICE_INTRO + "\n".join(f"\nDraft:\n{draft}\nOwner sent:\n{sent}" for draft, sent in examples)
    return SYSTEM.format(shop=settings.SHOP_NAME, channel=conversation.get_channel_display().lower(), voice=voice)


def build_prompt(conversation, message):
    earlier = list(conversation.messages.filter(pk__lt=message.pk).order_by("-pk")[:HISTORY])[::-1]
    lines = [f"Channel: {conversation.get_channel_display()}",
             f"Customer's email (as given, not verified): {conversation.email}"]
    if conversation.subject:
        lines.append("Email subject: " + wrap(conversation.subject, "email subject", 200))
    if earlier:
        lines.append("Conversation so far, oldest first:")
        for item in earlier:
            if item.sender == Message.Sender.CUSTOMER:
                lines.append("Customer: " + wrap(item.body, "customer", 2000))
            else:
                lines.append(f"{item.get_sender_display()}: {clean(item.body, 2000)}")
    lines.append(f"LATEST MESSAGE: {wrap(message.body, 'customer ' + conversation.channel)}")
    lines.append("Answer the latest message with reply, or hand it over with escalate.")
    return "\n".join(lines)


def screen(conversation, message):
    """Why the message goes to the owner without the AI, or ""."""
    text = message.body
    signals = injection_signals(text) + (injection_signals(conversation.subject) if conversation.subject else [])
    if signals:
        return "Looks like an attempt to manipulate the assistant (" + ", ".join(signals) + ")"
    if PERSON_RE.search(text):
        return "The customer asked for a person"
    topic = JUDGEMENT_RE.search(text) or JUDGEMENT_RE.search(conversation.subject or "")
    if topic:
        return f"Needs your judgement (mentions \"{topic.group(0)}\")"
    since = timezone.now() - timedelta(days=1)
    runs = Message.objects.filter(conversation__email__iexact=conversation.email, sender=Message.Sender.CUSTOMER,
                                  handled_at__gte=since).count()
    if runs >= settings.SUPPORT_AGENT_RUNS_PER_DAY:
        return f"More than {settings.SUPPORT_AGENT_RUNS_PER_DAY} messages from this address today"
    return ""


def answers_alone(category):
    return CategoryMode.objects.filter(category=category, answers_alone=True).exists()


def handle(message_id):
    message = Message.objects.select_related("conversation").filter(
        pk=message_id, sender=Message.Sender.CUSTOMER).first()
    if message is None or message.handled_at:
        return
    conversation = message.conversation
    with acting_as_agent(AGENT):
        message.handled_at = timezone.now()
        message.save(update_fields=["handled_at"])
        if conversation.status == Conversation.Status.ESCALATED:
            # Already the owner's; a follow-up just waits for them.
            record("support.followup_waiting", obj=conversation, message="Customer wrote again; waiting for you")
            return
        reason = screen(conversation, message)
        if reason:
            services.escalate(conversation, reason)
            return
        _run(conversation, message)


def _run(conversation, message):
    try:
        client = ai.client_for(AGENT, SupportStandIn)
        outcome = runner.run(AGENT, client, system=system_prompt(conversation),
                             prompt=build_prompt(conversation, message), tools=make_tools(conversation),
                             purpose=f"support:conversation:{conversation.pk}")
    except budget.BudgetExceeded as exc:
        services.escalate(conversation, f"AI spending cap reached: {exc}")
        return
    except ai.AIError as exc:
        log.warning("Support agent: AI call failed for conversation %s: %s", conversation.pk, exc)
        services.escalate(conversation, f"The AI service failed: {exc}"[:300])
        return
    if outcome.final == "escalate":
        services.escalate(conversation, "Assistant: " + clean(outcome.input["reason"], 250))
        return
    if outcome.final != "reply":
        services.escalate(conversation, "The assistant could not decide" if outcome.stopped == "turns"
                          else "The assistant answered without using reply")
        return
    category, text = outcome.input["category"], clean(outcome.input["text"], 3000)
    if category not in ANSWERABLE or not text:
        services.escalate(conversation, f"The assistant gave a reply in category {category!r}")
        return
    problems = output_problems(text)
    if problems:
        services.make_draft(conversation, Category(category), text)
        services.escalate(conversation, "Draft held back: " + "; ".join(problems))
        return
    if answers_alone(category):
        services.agent_answer(conversation, Category(category), text)
    else:
        services.make_draft(conversation, Category(category), text, acknowledge=True)
