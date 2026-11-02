"""Marketing on the owner dashboard's "Needs your attention" queue: posts
and articles to approve (kind "approvals"), posts whose time has come to
put up by hand, and posts that failed (kind "problems")."""

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from apps.core.attention import Attention

from .models import Post


def _when(moment):
    return timezone.localtime(moment).strftime("%a %b %-d, %-I:%M %p").replace(":00 ", " ")


def _about(post):
    text = " ".join(post.text.split())
    return text[:60] + ("..." if len(text) > 60 else "")


def attention_items():
    from apps.storefront.models import Article

    now = timezone.now()
    items = []
    drafts = list(Post.objects.waiting().order_by("scheduled_for", "pk"))
    if drafts:
        soon = [p for p in drafts if p.scheduled_for and p.scheduled_for <= now + timedelta(hours=24)]
        detail = "Nothing is posted until you approve what, where and when."
        if soon:
            detail = (f"{len(soon)} {'is' if len(soon) == 1 else 'are'} meant to go out by "
                      f"{_when(max(p.scheduled_for for p in soon))}.  ") + detail
        items.append(Attention(
            f"Posts waiting for your approval: {len(drafts)}", detail, reverse("marketing:home") + "#drafts",
            "urgent" if soon else "warning", kind="approvals", key="marketing:drafts",
            since=min(p.created_at for p in drafts)))
    articles = list(Article.objects.filter(is_published=False).exclude(written_by="owner").order_by("pk"))
    if articles:
        items.append(Attention(
            f"Tea notes articles drafted by the assistant: {len(articles)}",
            "Read, edit and publish them, or delete them (admin → Articles).", reverse("marketing:home") + "#articles",
            "warning", kind="approvals", key="marketing:articles"))
    for post in Post.objects.filter(status=Post.Status.DUE).order_by("scheduled_for"):
        items.append(Attention(
            f"Time to post on {post.get_network_display()}", f"\"{_about(post)}\", approved for "
            f"{_when(post.scheduled_for)}.  Copy it, post it, then mark it posted.", post.get_absolute_url(), "urgent",
            kind="approvals", key=f"marketing:due:{post.pk}", since=post.scheduled_for))
    for post in Post.objects.filter(status=Post.Status.FAILED).order_by("scheduled_for"):
        items.append(Attention(
            f"A {post.get_network_display()} post failed", post.error or "See the post.", post.get_absolute_url(),
            "urgent", kind="problems", key=f"marketing:failed:{post.pk}", since=post.scheduled_for))
    return items
