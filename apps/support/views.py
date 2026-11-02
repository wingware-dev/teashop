"""Support pages: the customer's chat (start it, the conversation, and the
JSON the page polls for replies), and the owner's inbox and conversation
pages."""

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.agents.labels import AI_LABEL, chat_notice
from apps.checkout import protection
from apps.checkout.views import shop_view
from apps.core.decorators import owner_required

from . import services
from .forms import ChatMessageForm, OwnerReplyForm, StartChatForm
from .models import ANSWERABLE, Category, CategoryMode, Conversation, Draft, Message


# -- The customer's chat -----------------------------------------------------------

def _chat_context(**extra):
    return {"chat_notice": chat_notice(), "ai_label": AI_LABEL, "support_email": settings.SUPPORT_EMAIL,
            **protection.context(), **extra}


@shop_view
@never_cache
@require_http_methods(["GET", "POST"])
def chat_start(request):
    form = StartChatForm(request.POST or None)
    if request.method == "POST":
        refused = protection.check(request, "support-chat", settings.SUPPORT_CHAT_RATE_LIMIT)
        if refused:
            messages.error(request, refused)
        elif form.is_valid():
            conversation = services.start_chat(form.cleaned_data["email"], form.cleaned_data["name"],
                                               form.cleaned_data["message"])
            return redirect(conversation.chat_url() + "#latest")
    return render(request, "support/chat_start.html", _chat_context(form=form))


def _chat(token):
    conversation = Conversation.objects.filter(token=token, channel=Conversation.Channel.CHAT).first()
    if conversation is None:
        raise Http404("No such chat")
    return conversation


def _visible(conversation):
    return list(conversation.messages.all())


def _waiting(conversation, chat_messages):
    """Whether the customer waits for the assistant (the page polls)."""
    return bool(chat_messages) and chat_messages[-1].sender == Message.Sender.CUSTOMER and \
        conversation.status == Conversation.Status.OPEN


@shop_view
@never_cache
@require_http_methods(["GET", "POST"])
def chat(request, token):
    conversation = _chat(token)
    form = ChatMessageForm(request.POST or None)
    if request.method == "POST":
        refused = protection.check(request, "support-chat", settings.SUPPORT_CHAT_RATE_LIMIT)
        if refused:
            messages.error(request, refused)
        elif form.is_valid():
            try:
                services.add_customer_message(conversation, form.cleaned_data["message"])
            except ValidationError as exc:
                messages.error(request, " ".join(exc.messages))
            else:
                return redirect(conversation.chat_url() + "#latest")
    chat_messages = _visible(conversation)
    return render(request, "support/chat.html", _chat_context(
        conversation=conversation, chat_messages=chat_messages, form=form,
        last_id=chat_messages[-1].pk if chat_messages else 0,
        waiting=_waiting(conversation, chat_messages),
        with_person=conversation.status in Conversation.WAITING))


@shop_view
@never_cache
@require_GET
def chat_messages(request, token):
    """New messages after ?after=<id>, for the chat page's script."""
    conversation = _chat(token)
    try:
        after = int(request.GET.get("after", 0))
    except ValueError:
        after = 0
    chat_messages = _visible(conversation)
    return JsonResponse({
        "messages": [{"id": m.pk, "sender": m.sender, "who": m.get_sender_display() if m.sender != "customer"
                      else "You", "ai": m.is_ai, "body": m.body, "at": m.created_at.isoformat()}
                     for m in chat_messages if m.pk > after],
        "waiting": _waiting(conversation, chat_messages),
    })


# -- The owner -----------------------------------------------------------------------

@never_cache
@owner_required
def owner_inbox(request):
    alone = set(CategoryMode.objects.filter(answers_alone=True).values_list("category", flat=True))
    categories = [(category, category in alone, services.readiness(category)) for category in ANSWERABLE]
    return render(request, "support/owner/inbox.html", {
        "escalated": Conversation.objects.filter(status=Conversation.Status.ESCALATED).order_by("escalated_at"),
        "drafted": Conversation.objects.filter(status=Conversation.Status.DRAFTED).order_by("last_activity_at"),
        "recent": Conversation.objects.exclude(status__in=Conversation.WAITING)[:30],
        "categories": categories,
        "min_drafts": settings.SUPPORT_READY_MIN_DRAFTS,
        "ready_percent": int(settings.SUPPORT_READY_RATE * 100),
        "inbox_on": bool(settings.SUPPORT_INBOX),
        "support_email": settings.SUPPORT_EMAIL,
    })


@never_cache
@owner_required
@require_http_methods(["GET", "POST"])
def owner_conversation(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk)
    draft = conversation.pending_draft()
    if request.method == "POST":
        form = OwnerReplyForm(request.POST)
        if form.is_valid():
            used = None
            if form.cleaned_data.get("draft"):
                used = Draft.objects.filter(pk=form.cleaned_data["draft"], conversation=conversation).first()
            try:
                services.owner_reply(conversation, form.cleaned_data["body"], draft=used)
            except ValidationError as exc:
                messages.error(request, " ".join(exc.messages))
            else:
                messages.success(request, f"Reply sent to {conversation.email}.")
                return redirect("support:owner_inbox")
    else:
        form = OwnerReplyForm(initial={"body": draft.body if draft else "", "draft": draft.pk if draft else None})
    return render(request, "support/owner/conversation.html", {
        "conversation": conversation, "chat_messages": conversation.messages.all(), "draft": draft, "form": form,
    })


@owner_required
@require_POST
def owner_discard_draft(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk)
    draft = conversation.pending_draft()
    if draft:
        services.discard_draft(draft)
        messages.info(request, "Draft discarded.  Write your own reply below.")
    return redirect(conversation.get_absolute_url())


@owner_required
@require_POST
def owner_close(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk)
    services.close(conversation)
    messages.info(request, "Conversation closed without a reply.")
    return redirect("support:owner_inbox")


@owner_required
@require_POST
def owner_category(request, category):
    if category not in Category.values:
        raise Http404("No such category")
    on = request.POST.get("answers_alone") == "1"
    try:
        services.set_answers_alone(Category(category), on)
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
    else:
        messages.success(request, f"{Category(category).label}: " + (
            "the assistant now answers these alone." if on else "back to watch mode (drafts for you)."))
    return redirect("support:owner_inbox")
