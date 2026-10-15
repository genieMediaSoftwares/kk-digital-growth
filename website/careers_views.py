"""Careers: public job listings and applications, plus job/application management
inside the custom admin (session-based, see views.admin_login_required)."""

import hashlib
import json
import logging

from django.contrib import messages
from django.core.cache import cache
from django.db import DatabaseError
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.html import escape
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .forms import JobApplicationForm, JobApplicationUpdateForm, JobOpeningForm
from .models import JobApplication, JobOpening
from .views import admin_login_required

logger = logging.getLogger(__name__)

SITE = "https://www.kkdigitalgrowth.com"

# Per-IP application limit (best effort: the default cache is per server instance).
APPLY_RATE_LIMIT = 5
APPLY_RATE_WINDOW = 60 * 60


def _is_admin(request):
    return bool(request.session.get('admin_id'))


def _noindex(response):
    response['X-Robots-Tag'] = 'noindex, nofollow'
    return response


def _closed_response(request, job):
    """A role that was public but is now closed or past its closing date: 410, no form."""
    response = render(request, 'careers/job_detail.html', {'job': job, 'closed': True}, status=410)
    return _noindex(response)


def _get_public_job(request, slug, allow_preview=False):
    """Return (job, preview). Drafts are 404 to the public; closed roles raise via 410."""
    job = get_object_or_404(JobOpening, slug=slug)
    if job.is_open:
        return job, False
    if allow_preview and _is_admin(request):
        return job, True
    if job.status == JobOpening.STATUS_DRAFT:
        raise Http404("Job opening not found")
    return job, None  # closed / expired


def _job_posting_json_ld(job):
    """schema.org JobPosting for an open role. Only fields an admin entered are included."""
    parts = [f"<p>{escape(job.summary)}</p>"]
    parts += [f"<p>{escape(p)}</p>" for p in job.description_paragraphs]
    for heading, items in (
        ("Responsibilities", job.responsibilities_list),
        ("Required skills", job.required_skills_list),
        ("Preferred skills", job.preferred_skills_list),
    ):
        if items:
            parts.append(f"<h3>{heading}</h3><ul>" + "".join(f"<li>{escape(i)}</li>" for i in items) + "</ul>")

    data = {
        "@context": "https://schema.org",
        "@type": "JobPosting",
        "title": job.title,
        "description": "".join(parts),
        "datePosted": (job.published_at or job.created_at).date().isoformat(),
        "url": f"{SITE}{job.get_absolute_url()}",
        "hiringOrganization": {
            "@type": "Organization",
            "@id": f"{SITE}/#organization",
            "name": "KK Digital Growth",
            "sameAs": f"{SITE}/",
        },
        "directApply": True,
    }
    if job.closing_date:
        data["validThrough"] = f"{job.closing_date.isoformat()}T23:59:59+05:30"
    if job.employment_type:
        data["employmentType"] = job.employment_type
    if job.work_mode == 'remote':
        data["jobLocationType"] = "TELECOMMUTE"
    if job.location:
        data["jobLocation"] = {
            "@type": "Place",
            "address": {"@type": "PostalAddress", "addressLocality": job.location},
        }
    if job.department:
        data["industry"] = job.department

    # Safe inside <script>: escape characters that could close the tag.
    raw = json.dumps(data, ensure_ascii=False, indent=2)
    return raw.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')


# --- Public pages ---

def careers(request):
    try:
        jobs = list(JobOpening.objects.open())
    except DatabaseError:
        # e.g. the careers migration has not been applied to this database yet
        logger.exception("Careers page: could not load job openings")
        jobs = []
    return render(request, 'careers/careers.html', {'jobs': jobs})


def career_detail(request, slug):
    job, preview = _get_public_job(request, slug, allow_preview=True)
    if preview is None:
        return _closed_response(request, job)
    context = {
        'job': job,
        'preview': preview,
        'job_posting_json_ld': None if preview else _job_posting_json_ld(job),
    }
    response = render(request, 'careers/job_detail.html', context)
    return _noindex(response) if preview else response


def _client_ip_key(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    ip = forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR', '')
    return 'careers-apply:' + hashlib.sha256(ip.encode()).hexdigest()[:32]


@never_cache
def career_apply(request, slug):
    job, preview = _get_public_job(request, slug)
    if preview is None:
        return _closed_response(request, job)

    submitted = request.session.pop('careers_applied', None) == job.slug
    error = None

    if request.method == 'POST':
        form = JobApplicationForm(request.POST)
        rate_key = _client_ip_key(request)
        attempts = cache.get(rate_key, 0)
        if attempts >= APPLY_RATE_LIMIT:
            error = "Too many applications have been sent from this connection. Please try again later."
        elif form.is_valid():
            cache.set(rate_key, attempts + 1, APPLY_RATE_WINDOW)
            data = form.cleaned_data
            duplicate = JobApplication.objects.filter(
                job=job, email__iexact=data['email'], message=data['message']).exists()
            if not form.is_spam and not duplicate:
                JobApplication.objects.create(
                    job=job,
                    job_title=job.title,
                    full_name=data['full_name'],
                    email=data['email'],
                    phone=data['phone'],
                    profile_url=data['profile_url'],
                    message=data['message'],
                    consent=True,
                )
            # Same response for spam and duplicates, so bots learn nothing.
            request.session['careers_applied'] = job.slug
            return redirect('career_apply', slug=job.slug)
    else:
        form = JobApplicationForm()

    response = render(request, 'careers/apply.html', {
        'job': job,
        'form': form,
        'submitted': submitted,
        'error': error,
    }, status=429 if error else 200)
    return _noindex(response)


# --- Admin: job openings ---

def _admin_context(request, **extra):
    context = {
        'admin_email': request.session.get('admin_email', 'Admin'),
        'admin_name': request.session.get('admin_name', 'Admin'),
    }
    context.update(extra)
    return context


@never_cache
@admin_login_required
def careers_admin_list(request):
    tab = request.GET.get('tab', 'all')
    jobs = JobOpening.objects.annotate(
        application_count=Count('applications'),
        new_count=Count('applications', filter=Q(applications__status='new')),
    ).order_by('display_order', '-updated_at')
    counts = {
        'all': JobOpening.objects.count(),
        'published': JobOpening.objects.filter(status='published').count(),
        'draft': JobOpening.objects.filter(status='draft').count(),
        'closed': JobOpening.objects.filter(status='closed').count(),
    }
    if tab in ('published', 'draft', 'closed'):
        jobs = jobs.filter(status=tab)
    else:
        tab = 'all'
    return _noindex(render(request, 'admin/careers_list.html', _admin_context(
        request,
        jobs=jobs,
        tab=tab,
        counts=counts,
        new_applications=JobApplication.objects.filter(status='new').count(),
    )))


@never_cache
@admin_login_required
def careers_admin_edit(request, job_id=None):
    job = get_object_or_404(JobOpening, pk=job_id) if job_id else None
    if request.method == 'POST':
        form = JobOpeningForm(request.POST, instance=job)
        if form.is_valid():
            job = form.save()
            messages.success(request, f"Job opening '{job.title}' saved ({job.get_status_display()}).")
            return redirect('careers_admin_list')
        messages.error(request, "Please correct the errors below.")
    else:
        form = JobOpeningForm(instance=job)
    return _noindex(render(request, 'admin/careers_form.html', _admin_context(
        request, form=form, job=job)))


@require_POST
@admin_login_required
def careers_admin_status(request, job_id):
    job = get_object_or_404(JobOpening, pk=job_id)
    action = request.POST.get('action')
    new_status = {
        'publish': JobOpening.STATUS_PUBLISHED,
        'unpublish': JobOpening.STATUS_DRAFT,
        'close': JobOpening.STATUS_CLOSED,
    }.get(action)
    if new_status:
        job.status = new_status
        job.save()
        messages.success(request, f"'{job.title}' is now {job.get_status_display().lower()}.")
    return redirect('careers_admin_list')


@require_POST
@admin_login_required
def careers_admin_delete(request, job_id):
    job = get_object_or_404(JobOpening, pk=job_id)
    title = job.title
    job.delete()
    messages.success(request, f"Job opening '{title}' deleted. Its applications were kept.")
    return redirect('careers_admin_list')


# --- Admin: applications ---

@never_cache
@admin_login_required
def careers_admin_applications(request):
    applications = JobApplication.objects.select_related('job')
    status = request.GET.get('status', '')
    job_id = request.GET.get('job', '')
    if status in dict(JobApplication.STATUS_CHOICES):
        applications = applications.filter(status=status)
    if job_id.isdigit():
        applications = applications.filter(job_id=int(job_id))
    return _noindex(render(request, 'admin/careers_applications.html', _admin_context(
        request,
        applications=applications,
        jobs=JobOpening.objects.order_by('title'),
        status_choices=JobApplication.STATUS_CHOICES,
        selected_status=status,
        selected_job=job_id,
    )))


@never_cache
@admin_login_required
def careers_admin_application_detail(request, application_id):
    application = get_object_or_404(JobApplication.objects.select_related('job'), pk=application_id)
    if request.method == 'POST':
        form = JobApplicationUpdateForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            messages.success(request, "Application updated.")
            return redirect('careers_admin_application_detail', application_id=application.pk)
    else:
        form = JobApplicationUpdateForm(instance=application)
    return _noindex(render(request, 'admin/careers_application_detail.html', _admin_context(
        request, application=application, form=form)))


@require_POST
@admin_login_required
def careers_admin_application_delete(request, application_id):
    application = get_object_or_404(JobApplication, pk=application_id)
    application.delete()
    messages.success(request, "Application permanently deleted.")
    return redirect('careers_admin_applications')
