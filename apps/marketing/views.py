"""The owner's marketing pages: the backlog and what waits, an idea, a
post (edit, check, approve), the calendar, campaigns, and an article draft
to publish."""

from datetime import date, timedelta

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST

from apps.agents.ai import is_live
from apps.core.decorators import owner_required
from apps.storefront.models import Article

from . import agent, guardrails, networks, publishers, services
from .forms import CampaignForm, DraftForm, IdeaForm, PostForm, PublishForm
from .jobs import run_agent
from .models import Campaign, Idea, Post


def _errors(request, exc):
    for message in exc.messages:
        messages.error(request, message)


def _network_status():
    return [(spec, publishers.posts_live(spec.name)) for spec in networks.NETWORKS.values()]


def _queued(request, job, what):
    if job is not None and job.status == "done":
        messages.success(request, f"The assistant {what}.")
    else:
        messages.info(request, f"The assistant is on it ({what}): reload this page in a minute.")


@never_cache
@owner_required
@require_http_methods(["GET", "POST"])
def home(request):
    form = IdeaForm(request.POST or None, prefix="idea")
    if request.method == "POST" and form.is_valid():
        idea = services.add_idea(form.cleaned_data["title"], form.cleaned_data["notes"],
                                 campaign=form.cleaned_data["campaign"], product=form.cleaned_data["product"])
        messages.success(request, f"Added to the backlog: {idea.title}")
        return redirect(idea.get_absolute_url())
    now = timezone.now()
    return render(request, "marketing/owner/home.html", {
        "form": form,
        "ideas": Idea.objects.filter(status__in=Idea.OPEN).select_related("product", "campaign"),
        "drafts": Post.objects.waiting().select_related("campaign"),
        "due": Post.objects.filter(status__in=(Post.Status.DUE, Post.Status.FAILED)),
        "upcoming": Post.objects.scheduled().filter(scheduled_for__lte=now + timedelta(days=14)),
        "articles": Article.objects.filter(is_published=False).order_by("-pk"),
        "posted": Post.objects.filter(status=Post.Status.POSTED).order_by("-posted_at")[:10],
        "network_status": _network_status(),
        "agent_live": is_live(agent.AGENT),
        "analytics": settings.ANALYTICS,
        "analytics_dashboard": settings.ANALYTICS_DASHBOARD_URL,
    })


@owner_required
@require_POST
def suggest(request):
    job = run_agent.enqueue("ideas")
    _queued(request, job, "suggested ideas: they are in the backlog, marked \"from the assistant\"")
    return redirect("marketing:home")


@never_cache
@owner_required
@require_http_methods(["GET", "POST"])
def idea(request, pk):
    idea = get_object_or_404(Idea.objects.select_related("product", "campaign"), pk=pk)
    form = IdeaForm(request.POST or None, instance=idea, prefix="idea")
    if request.method == "POST":
        action = request.POST.get("action", "save")
        if action in ("done", "dismissed", "new"):
            services.set_idea_status(idea, action)
            messages.success(request, f"Marked {idea.get_status_display().lower()}.")
            return redirect("marketing:home" if action != "new" else idea.get_absolute_url())
        if form.is_valid():
            form.save()
            messages.success(request, "Saved.")
            return redirect(idea.get_absolute_url())
    draft_form = DraftForm(initial={"when": timezone.localtime(services.next_slot()), "campaign": idea.campaign},
                           prefix="draft")
    return render(request, "marketing/owner/idea.html", {
        "idea": idea, "form": form, "draft_form": draft_form, "posts": idea.posts.all(),
        "articles": idea.articles.all(), "mailings": idea.mailings.all(), "agent_live": is_live(agent.AGENT)})


@owner_required
@require_POST
def idea_draft(request, pk):
    idea = get_object_or_404(Idea, pk=pk)
    task = request.POST.get("task")
    if task == "posts":
        form = DraftForm(request.POST, prefix="draft")
        if not form.is_valid() or not form.cleaned_data["networks"]:
            for errors in form.errors.values():
                for error in errors:
                    messages.error(request, error)
            if form.is_valid():
                messages.error(request, "Choose at least one network.")
            return redirect(idea.get_absolute_url())
        campaign = form.cleaned_data["campaign"]
        job = run_agent.enqueue("posts", idea.pk, list(form.cleaned_data["networks"]),
                                campaign.pk if campaign else None, form.cleaned_data["when"].isoformat())
        _queued(request, job, "drafted the posts below")
    elif task in ("article", "mailing"):
        job = run_agent.enqueue(task, idea.pk)
        _queued(request, job, "drafted a tea notes article" if task == "article"
                else "drafted an email, now waiting on the email list's page")
    else:
        messages.error(request, "Unknown request.")
    idea.refresh_from_db()
    if idea.agent_note:
        messages.warning(request, idea.agent_note)
    return redirect(idea.get_absolute_url() + "#drafted")


@never_cache
@owner_required
@require_http_methods(["GET", "POST"])
def post_new(request):
    idea = Idea.objects.filter(pk=request.GET.get("idea") or 0).first()
    initial = {"scheduled_for": timezone.localtime(services.next_slot())}
    if idea:
        initial.update(campaign=idea.campaign, product=idea.product,
                       link=idea.product.get_absolute_url() if idea.product else "")
    form = PostForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        post = form.save(commit=False)
        post.idea, post.made_by = idea, "owner"
        post = services.new_post(post)
        messages.success(request, "Saved as a draft.  Check it below, then approve it.")
        return redirect(post.get_absolute_url())
    return render(request, "marketing/owner/post_new.html", {"form": form, "idea": idea})


@never_cache
@owner_required
@require_http_methods(["GET", "POST"])
def post(request, pk):
    post = get_object_or_404(Post.objects.select_related("photo", "campaign", "product", "idea"), pk=pk)
    editable = post.status in (Post.Status.DRAFT, Post.Status.APPROVED, Post.Status.REJECTED)
    form = PostForm(instance=post) if editable else None
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "save" and editable:
                form = PostForm(request.POST, instance=Post.objects.get(pk=post.pk))
                if form.is_valid():
                    changes = {name: form.cleaned_data[name] for name in services.POST_FIELDS}
                    was = post.status
                    if services.update_post(post, changes, request.user):
                        messages.success(request, "Saved." + (" It is a draft again: approve it again to schedule "
                                                              "it." if was == Post.Status.APPROVED else ""))
                    return redirect(post.get_absolute_url())
            elif action == "approve":
                services.approve(post, request.user)
                messages.success(request, "Approved." + (" It posts itself at its time." if post.is_live else
                                                         " At its time it comes to your dashboard to post."))
                return redirect(post.get_absolute_url())
            elif action == "reject":
                services.reject(post, request.user, request.POST.get("note", ""))
                messages.success(request, "Rejected.")
                return redirect("marketing:home")
            elif action == "withdraw":
                services.withdraw(post, request.user)
                messages.success(request, "Taken off the schedule; it is a draft again.")
                return redirect(post.get_absolute_url())
            elif action == "posted":
                services.mark_posted(post, request.user, request.POST.get("url", "").strip())
                messages.success(request, "Marked as posted.")
                return redirect("marketing:home")
            elif action == "retry":
                services.try_again(post, request.user)
                post.refresh_from_db()
                messages.info(request, f"Tried again: {post.get_status_display().lower()}.")
                return redirect(post.get_absolute_url())
            else:
                messages.error(request, "That can't be done to this post now.")
        except ValidationError as exc:
            _errors(request, exc)
    return render(request, "marketing/owner/post.html", {
        "post": post, "form": form, "problems": guardrails.problems(post), "warnings": guardrails.warnings(post),
        "spec": post.spec, "final_text": post.final_text(), "length": post.length()})


def _month(request):
    today = timezone.localdate()
    try:
        year, month = (int(part) for part in request.GET.get("month", "").split("-"))
        return date(year, month, 1)
    except ValueError:
        return today.replace(day=1)


@never_cache
@owner_required
def calendar(request):
    first = _month(request)
    previous = (first - timedelta(days=1)).replace(day=1)
    following = (first + timedelta(days=32)).replace(day=1)
    return render(request, "marketing/owner/calendar.html", {
        "first": first, "weeks": services.month_calendar(first.year, first.month), "today": timezone.localdate(),
        "previous": previous, "following": following,
        "unscheduled": Post.objects.waiting().filter(scheduled_for=None),
        "campaigns": [c for c in Campaign.objects.all() if (not c.ends_on or c.ends_on >= first)
                      and (not c.starts_on or c.starts_on < following)],
    })


@never_cache
@owner_required
@require_http_methods(["GET", "POST"])
def campaigns(request):
    form = CampaignForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        campaign = form.save()
        messages.success(request, f"Campaign {campaign.name} saved.")
        return redirect(campaign.get_absolute_url())
    return render(request, "marketing/owner/campaigns.html", {
        "form": form, "campaigns": [(c, c.results()) for c in Campaign.objects.prefetch_related("codes")]})


@never_cache
@owner_required
@require_http_methods(["GET", "POST"])
def campaign(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    form = CampaignForm(request.POST or None, instance=campaign)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Saved.")
        return redirect(campaign.get_absolute_url())
    return render(request, "marketing/owner/campaign.html", {
        "campaign": campaign, "form": form, "results": campaign.results(), "posts": campaign.posts.all(),
        "ideas": campaign.ideas.all(), "analytics_dashboard": settings.ANALYTICS_DASHBOARD_URL})


@never_cache
@owner_required
@require_http_methods(["GET", "POST"])
def article(request, pk):
    article = get_object_or_404(Article, pk=pk)
    form = PublishForm(request.POST or None)
    if request.method == "POST":
        try:
            if request.POST.get("action") == "unpublish":
                services.unpublish_article(article, request.user)
                messages.success(request, "Taken out of Tea notes.")
                return redirect(request.path)
            if form.is_valid():
                services.publish_article(article, request.user, form.cleaned_data["day"])
                messages.success(request, f"Published: it appears in Tea notes from "
                                          f"{article.published_on:%B %-d}.")
                return redirect(request.path)
        except ValidationError as exc:
            _errors(request, exc)
    paragraphs = [(p[3:].strip(), True) if p.startswith("## ") else (p.strip(), False)
                  for p in article.body.split("\n\n") if p.strip()]
    return render(request, "marketing/owner/article.html", {
        "article": article, "form": form, "paragraphs": paragraphs, "today": timezone.localdate(),
        "problems": services.article_problems(article) if not article.is_published else []})
