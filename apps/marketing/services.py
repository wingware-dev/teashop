"""What changes marketing records: ideas, post edits, approval, the
schedule and posting, and publishing tea notes articles.

The owner approves each post's what, where and when together; AI agents
can draft but never approve or publish (PermissionDenied, whatever their
prompt says).  Approved posts go out from the job queue: a sweep every few
minutes (jobs.py) posts the ones whose time has come through the
network's API when it is turned on, and puts the rest on the owner's
dashboard to post by hand.
"""

import calendar as calendar_module
import logging
from datetime import date, datetime, time, timedelta

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps import jobs
from apps.audit import current_actor, record

from . import guardrails, publishers
from .models import Idea, Post

log = logging.getLogger(__name__)

POST_FIELDS = ("network", "text", "title", "link", "photo", "gift", "scheduled_for", "campaign", "product")


def _refuse_agents(what):
    if current_actor().type == "agent":
        raise PermissionDenied(f"AI agents cannot {what}; only the owner can.")


def _owner(user):
    if user is None or not user.is_authenticated or not user.is_staff:
        raise PermissionDenied("Only the owner can do this.")


# -- Ideas -----------------------------------------------------------------------------

def add_idea(title, notes="", *, campaign=None, product=None, made_by="owner"):
    idea = Idea.objects.create(title=title.strip()[:150], notes=notes.strip(), campaign=campaign, product=product,
                               made_by=made_by)
    record("marketing.idea_added", obj=idea, message=idea.title)
    return idea


def set_idea_status(idea, status):
    idea.status = status
    idea.save(update_fields=["status"])
    record("marketing.idea_" + status, obj=idea)


# -- Posts -----------------------------------------------------------------------------

def new_post(post=None, **fields):
    """Save a new draft post (an unsaved Post, or its fields)."""
    post = post or Post(**fields)
    post.status = Post.Status.DRAFT
    post.full_clean()
    post.save()
    record("marketing.post_drafted", obj=post, message=f"{post.get_network_display()}, by {post.made_by}")
    return post


def update_post(post, changes, user=None):
    """The owner edits a post.  Any change to an approved post takes it back
    to a draft, since approval covers what, where and when."""
    if post.status not in (Post.Status.DRAFT, Post.Status.APPROVED, Post.Status.REJECTED):
        raise ValidationError(f"It is {post.get_status_display().lower()}; it can't be changed now.")
    changed = [name for name in POST_FIELDS if name in changes and getattr(post, name) != changes[name]]
    if not changed:
        return False
    for name in changed:
        setattr(post, name, changes[name])
    post.full_clean()
    if current_actor().type != "agent" and post.from_agent and any(n in changed for n in ("text", "title")):
        post.edited_by_owner = True
    was = post.status
    if was in (Post.Status.APPROVED, Post.Status.REJECTED):
        post.status, post.approved_at, post.approved_by = Post.Status.DRAFT, None, None
    post.save()
    record("marketing.post_edited", obj=post, message=", ".join(changed) +
           (" (approval withdrawn: approve it again)" if was == Post.Status.APPROVED else ""))
    return True


def approve(post, user, now=None):
    """The owner approves the post to go out on its network at its time."""
    _refuse_agents("approve posts")
    _owner(user)
    now = now or timezone.now()
    if post.status != Post.Status.DRAFT:
        raise ValidationError(f"It is {post.get_status_display().lower()}, not a draft.")
    problems = guardrails.problems(post)
    if post.scheduled_for and post.scheduled_for < now - timedelta(minutes=5):
        problems.append("Its time has passed: pick a new one.")
    if problems:
        raise ValidationError(problems)
    post.status, post.approved_at, post.approved_by, post.error = Post.Status.APPROVED, now, user, ""
    post.save(update_fields=["status", "approved_at", "approved_by", "error"])
    how = "posts itself" if post.is_live else "you post it by hand"
    record("marketing.post_approved", obj=post,
           message=f"{post.get_network_display()} at {timezone.localtime(post.scheduled_for):%Y-%m-%d %H:%M} ({how})")


def withdraw(post, user):
    """Take an approved post off the schedule (back to a draft)."""
    _owner(user)
    if post.status not in (Post.Status.APPROVED, Post.Status.DUE, Post.Status.FAILED):
        raise ValidationError("Only a scheduled post can be withdrawn.")
    post.status, post.approved_at, post.approved_by = Post.Status.DRAFT, None, None
    post.save(update_fields=["status", "approved_at", "approved_by"])
    record("marketing.post_withdrawn", obj=post)


def reject(post, user, note=""):
    _owner(user)
    if post.status != Post.Status.DRAFT:
        raise ValidationError("Only a draft can be rejected.")
    post.status = Post.Status.REJECTED
    post.save(update_fields=["status"])
    record("marketing.post_rejected", obj=post, message=note[:300])


def mark_posted(post, user, url=""):
    """The owner put up a by-hand post (or one that failed, themselves)."""
    _refuse_agents("mark posts as posted")
    _owner(user)
    if post.status not in (Post.Status.DUE, Post.Status.APPROVED, Post.Status.FAILED):
        raise ValidationError("Only an approved post can be marked posted.")
    post.status, post.posted_at, post.external_url, post.error = Post.Status.POSTED, timezone.now(), url[:500], ""
    post.full_clean()
    post.save(update_fields=["status", "posted_at", "external_url", "error"])
    record("marketing.post_posted", obj=post, message=f"By hand{': ' + url if url else ''}")


def try_again(post, user, now=None):
    """A failed post goes out again at once (it is still approved)."""
    _owner(user)
    if post.status != Post.Status.FAILED:
        raise ValidationError("Only a post that failed can be tried again.")
    post.status, post.scheduled_for, post.error = Post.Status.APPROVED, now or timezone.now(), ""
    post.save(update_fields=["status", "scheduled_for", "error"])
    record("marketing.post_retried", obj=post)
    publish_due(now=post.scheduled_for)


def _fail(post, message):
    post.status, post.error = Post.Status.FAILED, message[:500]
    post.save(update_fields=["status", "error"])
    record("marketing.post_failed", obj=post, message=post.error)
    log.warning("Marketing: post %s failed: %s", post.pk, message)


def publish_due(now=None):
    """Approved posts whose time has come: queue each live one's posting
    (its own job, so each retries alone), make by-hand ones due for the
    owner.  A live post more than MARKETING_POST_GRACE late isn't posted
    (it may be stale): it fails, for the owner to decide."""
    from .jobs import publish_post

    now = now or timezone.now()
    grace = timedelta(hours=settings.MARKETING_POST_GRACE_HOURS)
    for post in Post.objects.scheduled().filter(scheduled_for__lte=now):
        if not post.is_live:
            post.status = Post.Status.DUE
            post.save(update_fields=["status"])
            record("marketing.post_due", obj=post, message=f"Time to post it on {post.get_network_display()}")
        elif post.scheduled_for < now - grace:
            _fail(post, f"It wasn't posted within {settings.MARKETING_POST_GRACE_HOURS} hours of its time (was the "
                        f"worker stopped?), so it was held back in case it is stale.")
        else:
            jobs.enqueue(publish_post, post.pk, key=f"marketing:publish:{post.pk}")


RETRY_EVERY = timedelta(minutes=10)


def publish(post_id, now=None):
    """Post one approved, due post through its network's API (the job)."""
    now = now or timezone.now()
    post = Post.objects.select_for_update().filter(pk=post_id).select_related("photo", "campaign").first()
    if post is None or post.status != Post.Status.APPROVED or not post.scheduled_for or post.scheduled_for > now:
        return  # withdrawn, edited, already posted, or not yet: nothing to do
    if not post.is_live:
        return
    problems = guardrails.problems(post)
    if problems:
        _fail(post, "It no longer passes the checks: " + " ".join(problems))
        return
    try:
        external_id, url = publishers.publish(post)
    except publishers.PostingUnavailable as exc:
        if post.scheduled_for < now - timedelta(hours=settings.MARKETING_POST_GRACE_HOURS):
            _fail(post, str(exc))
            return
        raise jobs.Retry(str(exc), delay=RETRY_EVERY) from exc
    except publishers.PostingError as exc:
        _fail(post, str(exc))
        return
    post.status, post.posted_at, post.external_id, post.external_url = Post.Status.POSTED, now, external_id, url
    post.save(update_fields=["status", "posted_at", "external_id", "external_url"])
    record("marketing.post_posted", obj=post, message=f"Through the {post.get_network_display()} API: {url or external_id}")


# -- Tea notes articles ----------------------------------------------------------------

def article_problems(article):
    problems = guardrails.article_problems(article.title, article.summary, article.body,
                                           by_agent=article.written_by != "owner")
    try:
        article.full_clean()
    except ValidationError as exc:
        problems += [message for message in exc.messages if message not in problems]
    return problems


@transaction.atomic
def publish_article(article, user, day):
    """The owner publishes an article in the tea notes section from day
    (today, or a later day: it appears then)."""
    _refuse_agents("publish articles")
    _owner(user)
    if article.is_published:
        raise ValidationError("It is already published.")
    problems = article_problems(article)
    if day < timezone.localdate():
        problems.append("Pick today or a later day.")
    if problems:
        raise ValidationError(problems)
    article.is_published, article.published_on = True, day
    article.save(update_fields=["is_published", "published_on", "updated_at"])
    record("marketing.article_published", obj=article, message=f"From {day.isoformat()}")


def unpublish_article(article, user):
    _owner(user)
    article.is_published = False
    article.save(update_fields=["is_published", "updated_at"])
    record("marketing.article_unpublished", obj=article)


# -- The calendar ---------------------------------------------------------------------

def default_time(day):
    """A post's default time on day: MARKETING_POST_AT, local time."""
    hour, minute = (int(part) for part in settings.MARKETING_POST_AT.split(":"))
    return timezone.make_aware(datetime.combine(day, time(hour, minute)))


def next_slot(now=None):
    """The next default posting time at least an hour from now."""
    now = timezone.localtime(now or timezone.now())
    day = now.date()
    while default_time(day) < now + timedelta(hours=1):
        day += timedelta(days=1)
    return default_time(day)


def month_calendar(year, month):
    """[[(date or None, [items])] per week] for the month: posts by their
    local day, and articles by the day they appear."""
    from apps.storefront.models import Article

    first = date(year, month, 1)
    last = date(year, month, calendar_module.monthrange(year, month)[1])
    start = timezone.make_aware(datetime.combine(first, time.min))
    end = timezone.make_aware(datetime.combine(last + timedelta(days=1), time.min))
    by_day = {}
    posts = Post.objects.filter(scheduled_for__gte=start, scheduled_for__lt=end).exclude(
        status=Post.Status.REJECTED).select_related("campaign")
    for post in posts:
        by_day.setdefault(timezone.localdate(post.scheduled_for), []).append(("post", post))
    for article in Article.objects.filter(is_published=True, published_on__range=(first, last)):
        by_day.setdefault(article.published_on, []).append(("article", article))
    weeks = []
    for week in calendar_module.Calendar(firstweekday=0).monthdatescalendar(year, month):
        weeks.append([(day if day.month == month else None,
                       sorted(by_day.get(day, []), key=lambda item: (
                           item[0] != "post", item[1].scheduled_for if item[0] == "post" else start, item[1].pk)))
                      for day in week])
    return weeks
