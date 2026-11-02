"""Marketing's jobs (apps.jobs imports this at startup; see docs/jobs.md):
the posting sweep, each post's posting, the agent's drafting runs and its
weekly ideas."""

from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone

from apps import jobs


@jobs.job(max_attempts=2)
def publish_due_posts():
    """Every few minutes: approved posts whose time has come go out (live)
    or to the owner's dashboard (by hand)."""
    from . import services

    services.publish_due()


# About MARKETING_POST_GRACE_HOURS of retries, 10 minutes apart, when the
# network is down; services.publish() then marks the post failed.
@jobs.job(max_attempts=40, retry_delay=timedelta(minutes=10))
def publish_post(post_id):
    """Post one approved post through its network's API."""
    from . import services

    services.publish(post_id)


@jobs.job(max_attempts=2)
def run_agent(task, idea_id=None, networks=(), campaign_id=None, when=None):
    """The marketing agent drafts from an idea, or suggests ideas.  The
    outcome is in the audit log, and a problem is kept on the idea."""
    from . import agent
    from .models import Campaign, Idea

    if task == "ideas":
        agent.suggest_ideas()
        return
    idea = Idea.objects.filter(pk=idea_id).first()
    if idea is None:
        return
    if task == "posts":
        campaign = Campaign.objects.filter(pk=campaign_id).first() if campaign_id else None
        moment = datetime.fromisoformat(when) if when else None
        result = agent.draft_posts(idea, list(networks), campaign=campaign, when=moment)
    elif task == "article":
        result = agent.draft_article(idea)
    elif task == "mailing":
        result = agent.draft_mailing(idea)
    else:
        raise ValueError(f"No marketing task {task!r}")
    idea.agent_note = result.problem[:300]
    idea.save(update_fields=["agent_note"])


@jobs.job(max_attempts=2)
def weekly_ideas():
    """Once a day: if the agent last suggested ideas a week ago or more and
    the backlog is short, it suggests some."""
    from .models import Idea

    if not settings.MARKETING_WEEKLY_IDEAS:
        return
    week_ago = timezone.now() - timedelta(days=7)
    if Idea.objects.exclude(made_by="owner").filter(created_at__gte=week_ago).exists():
        return
    if Idea.objects.filter(status=Idea.Status.NEW).count() >= 10:
        return
    from . import agent

    agent.suggest_ideas()


jobs.schedule(publish_due_posts, every=timedelta(minutes=settings.MARKETING_SWEEP_MINUTES))
jobs.schedule(weekly_ideas, daily_at="07:30")
