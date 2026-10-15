import json
import re
from html import unescape

from django.test import SimpleTestCase
from django.urls import reverse

SITE = "https://www.kkdigitalgrowth.com"

# Service category landing pages (one per group in the Services mega-menu)
CATEGORY_PAGES = {
    "service_software_engineering": "/services/software-engineering/",
    "service_enterprise_systems": "/services/enterprise-business-systems/",
    "service_ai_solutions": "/services/ai-solutions/",
    "service_product_design": "/services/experience-product-design/",
    "service_cloud_devops": "/services/cloud-devops/",
    "service_digital_marketing": "/services/digital-marketing/",
}

SERVICE_PAGES = {
    "services": "/services/",
    "service_web_development": "/services/web-development/",
    "service_mobile_app_development": "/services/mobile-app-development/",
    "service_custom_software": "/services/custom-software-development/",
    "service_erp_development": "/services/erp-development/",
    "service_ui_ux_design": "/services/ui-ux-design/",
    "service_seo": "/services/seo-services/",
    "location_visakhapatnam": "/locations/visakhapatnam/",
    **CATEGORY_PAGES,
}


def main_html(html):
    return re.search(r"<main[^>]*>(.*)</main>", html, re.S).group(1)


class ServicePagesTests(SimpleTestCase):
    """Service catalogue pages render without the database."""

    def get_html(self, path):
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200, path)
        return response.content.decode()

    def test_urls_are_unchanged(self):
        for name, path in SERVICE_PAGES.items():
            self.assertEqual(reverse(name), path)

    def test_head_tags_and_single_h1(self):
        titles, descriptions = set(), set()
        for path in SERVICE_PAGES.values():
            html = self.get_html(path)
            title = re.search(r"<title>(.*?)</title>", html, re.S).group(1).strip()
            desc = re.search(r'<meta name="description" content="([^"]{50,})">', html).group(1)
            self.assertNotIn(title, titles, f"duplicate title on {path}")
            self.assertNotIn(desc, descriptions, f"duplicate description on {path}")
            titles.add(title)
            descriptions.add(desc)
            self.assertIn(f'<link rel="canonical" href="{SITE}{path}">', html)
            self.assertIn(f'<meta property="og:url" content="{SITE}{path}">', html)
            self.assertEqual(len(re.findall(r"<h1[\s>]", html)), 1, path)
            self.assertNotIn('name="keywords"', html)

    def test_json_ld_is_valid(self):
        for path in SERVICE_PAGES.values():
            html = self.get_html(path)
            blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
            self.assertTrue(blocks, path)
            for block in blocks:
                data = json.loads(block)
                self.assertNotIn("aggregateRating", json.dumps(data), path)

    def test_header_catalogue_links_resolve(self):
        html = self.get_html("/services/")
        menu = re.search(r'<div class="svc-mega" id="services-mega">(.*?)<!-- ================= RIGHT SIDE', html, re.S).group(1)
        hrefs = set(re.findall(r'href="([^"]+)"', menu))
        # each category title links to its own landing page
        for path in CATEGORY_PAGES.values():
            self.assertIn(path, hrefs)
        pages = {}
        for href in hrefs:
            path, _, fragment = href.partition("#")
            if path == "/careers/":
                continue  # needs the database; covered by CareersPublicTests
            if path not in pages:
                pages[path] = self.get_html(path)
            if fragment:
                self.assertIn(f'id="{fragment}"', pages[path], href)

    def test_mobile_menu_category_links(self):
        html = self.get_html("/about/")
        for name, path in CATEGORY_PAGES.items():
            self.assertRegex(html, rf'<a class="m-svc-cat" href="{re.escape(path)}"')
        self.assertEqual(html.count('class="m-svc-toggle" aria-expanded="false"'), 6)

    def test_services_toggle_is_separate_from_overview_link(self):
        html = self.get_html("/about/")
        self.assertRegex(html, r'<a href="/services/"\s+class="nav-services-link')
        self.assertIn('id="services-dropdown-btn"', html)
        self.assertIn('aria-controls="services-mega"', html)

    def test_overview_links_every_category_and_keeps_old_anchors(self):
        main = main_html(self.get_html("/services/"))
        for path in CATEGORY_PAGES.values():
            self.assertIn(f'href="{path}"', main)
        for anchor in ("software-engineering", "business-systems", "ai-systems", "product-design",
                       "cloud-devops", "organic-growth", "website-development", "mobile-app-development",
                       "erp-development", "custom-application-development", "ui-ux-design"):
            self.assertIn(f'id="{anchor}"', main)

    def test_category_pages_stay_within_their_category(self):
        for path in CATEGORY_PAGES.values():
            main = main_html(self.get_html(path))
            for other in CATEGORY_PAGES.values():
                if other == path:
                    continue
                # a single, contextual link is allowed (e.g. AI -> workflow automation);
                # a list of other categories is not
                self.assertLessEqual(main.count(f'href="{other}'), 1, f"{path} links to {other}")
            self.assertLessEqual(sum(main.count(f'href="{o}') for o in CATEGORY_PAGES.values() if o != path), 1, path)

    def test_unknown_service_returns_404(self):
        self.assertEqual(self.client.get("/services/does-not-exist/").status_code, 404)


class CrawlFilesTests(SimpleTestCase):
    def test_sitemap_lists_service_pages(self):
        body = self.client.get("/sitemap.xml").content.decode()
        for path in SERVICE_PAGES.values():
            self.assertIn(f"{path}</loc>", body)
        self.assertNotIn("/admin/", body)
        self.assertNotIn("#", body)

    def test_robots_keeps_services_crawlable(self):
        body = self.client.get("/robots.txt").content.decode()
        self.assertIn("Sitemap: https://www.kkdigitalgrowth.com/sitemap.xml", body)
        self.assertNotIn("Disallow: /services", body)


# --- Careers ---
# These use the database: run with USE_LOCAL_DB=1 so the test database is SQLite.

import datetime

from django.core.cache import cache
from django.test import Client, TestCase
from django.utils import timezone

from website.forms import JobApplicationForm
from website.models import JobApplication, JobOpening


def make_job(**kwargs):
    defaults = {
        "title": "Python Developer",
        "slug": "python-developer",
        "summary": "Build and maintain Django applications for client projects.",
        "status": JobOpening.STATUS_PUBLISHED,
    }
    defaults.update(kwargs)
    return JobOpening.objects.create(**defaults)


def valid_application(**kwargs):
    data = {
        "full_name": "Test Applicant",
        "email": "applicant@example.com",
        "phone": "+91 90000 00000",
        "profile_url": "https://example.com/cv",
        "message": "I have three years of Django experience building business apps.",
        "consent": "on",
        "website": "",
        "form_ts": JobApplicationForm().initial["form_ts"],
    }
    data.update(kwargs)
    return data


class CareersTestMixin:
    def setUp(self):
        cache.clear()
        # the application form treats submissions made in under MIN_SECONDS as spam
        self._min_seconds = JobApplicationForm.MIN_SECONDS
        JobApplicationForm.MIN_SECONDS = 0

    def tearDown(self):
        JobApplicationForm.MIN_SECONDS = self._min_seconds

    def login_admin(self, client=None):
        client = client or self.client
        session = client.session
        session["admin_id"] = 1
        session["admin_email"] = "admin@example.com"
        session.save()
        return client


class CareersPublicTests(CareersTestMixin, TestCase):

    def test_careers_page_renders_with_seo_tags(self):
        response = self.client.get("/careers/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertEqual(reverse("careers"), "/careers/")
        self.assertIn("<title>Careers at KK Digital Growth | Jobs in Visakhapatnam</title>", html)
        self.assertIn(f'<link rel="canonical" href="{SITE}/careers/">', html)
        self.assertIn(f'<meta property="og:url" content="{SITE}/careers/">', html)
        self.assertEqual(len(re.findall(r"<h1[\s>]", html)), 1)
        self.assertNotIn('"JobPosting"', html)
        self.assertNotIn("{#", html)  # template comments must not leak into the page
        for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
            json.loads(block)

    def test_empty_state_when_no_open_roles(self):
        make_job(slug="draft-role", status=JobOpening.STATUS_DRAFT)
        html = self.client.get("/careers/").content.decode()
        self.assertIn("No open roles right now", html)
        self.assertNotIn("draft-role", html)

    def test_only_open_published_roles_are_listed(self):
        make_job(title="Open Role", slug="open-role")
        make_job(title="Draft Role", slug="draft-role", status=JobOpening.STATUS_DRAFT)
        make_job(title="Closed Role", slug="closed-role", status=JobOpening.STATUS_CLOSED)
        make_job(title="Expired Role", slug="expired-role",
                 closing_date=timezone.localdate() - datetime.timedelta(days=1))
        make_job(title="Closes Today", slug="closes-today", closing_date=timezone.localdate())
        main = main_html(self.client.get("/careers/").content.decode())
        self.assertIn("Open Role", main)
        self.assertIn("Closes Today", main)
        for hidden in ("Draft Role", "Closed Role", "Expired Role"):
            self.assertNotIn(hidden, main)

    def test_card_shows_only_entered_fields(self):
        make_job(slug="bare", title="Bare Role", display_order=0)
        make_job(slug="full", title="Full Role", department="Engineering", location="Visakhapatnam",
                 work_mode="hybrid", employment_type="FULL_TIME", display_order=1)
        main = main_html(self.client.get("/careers/").content.decode())
        bare_card = main.split("Bare Role")[1].split("Full Role")[0]
        self.assertNotIn("careers-meta", bare_card)
        self.assertIn("Engineering", main)
        self.assertIn("Hybrid", main)
        self.assertIn("Full-time", main)

    def test_display_order(self):
        make_job(title="Second", slug="second", display_order=2)
        make_job(title="First", slug="first", display_order=1)
        main = main_html(self.client.get("/careers/").content.decode())
        self.assertLess(main.index(">First<"), main.index(">Second<"))

    def test_detail_page_for_open_role(self):
        job = make_job(description="Para one.\n\nPara two.", responsibilities="Build APIs\n- Review code",
                       required_skills="Python", employment_type="FULL_TIME", location="Visakhapatnam",
                       closing_date=timezone.localdate() + datetime.timedelta(days=10))
        response = self.client.get(f"/careers/{job.slug}/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertEqual(len(re.findall(r"<h1[\s>]", html)), 1)
        self.assertIn(f'<link rel="canonical" href="{SITE}/careers/{job.slug}/">', html)
        self.assertIn("<li>Review code</li>", html)
        self.assertNotIn("Preferred skills", html)
        self.assertIn(f'href="/careers/{job.slug}/apply/"', html)
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
        postings = [d for d in map(json.loads, blocks) if d.get("@type") == "JobPosting"]
        self.assertEqual(len(postings), 1)
        posting = postings[0]
        self.assertEqual(posting["title"], job.title)
        self.assertEqual(posting["employmentType"], "FULL_TIME")
        self.assertIn("validThrough", posting)
        self.assertNotIn("baseSalary", posting)

    def test_job_posting_json_ld_escapes_script_breakers(self):
        job = make_job(summary="Uses </script><b>tags</b> & more in the summary text here.")
        html = self.client.get(f"/careers/{job.slug}/").content.decode()
        self.assertNotIn("</script><b>", html)

    def test_unknown_and_draft_roles_return_404(self):
        make_job(slug="draft-role", status=JobOpening.STATUS_DRAFT)
        for path in ("/careers/does-not-exist/", "/careers/draft-role/",
                     "/careers/draft-role/apply/", "/careers/does-not-exist/apply/"):
            self.assertEqual(self.client.get(path).status_code, 404, path)

    def test_closed_and_expired_roles_are_gone_without_form(self):
        make_job(slug="closed-role", status=JobOpening.STATUS_CLOSED)
        make_job(slug="expired-role", closing_date=timezone.localdate() - datetime.timedelta(days=1))
        for slug in ("closed-role", "expired-role"):
            for path in (f"/careers/{slug}/", f"/careers/{slug}/apply/"):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 410, path)
                html = response.content.decode()
                self.assertIn("no longer open", html)
                self.assertIn('content="noindex', html)
                self.assertNotIn("<form", main_html(html))
                self.assertNotIn('"JobPosting"', html)

    def test_admin_can_preview_draft(self):
        make_job(slug="draft-role", status=JobOpening.STATUS_DRAFT)
        self.login_admin()
        response = self.client.get("/careers/draft-role/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("Admin preview", html)
        self.assertIn('content="noindex', html)
        self.assertNotIn('"JobPosting"', html)
        self.assertNotIn("/careers/draft-role/apply/", html)

    def test_nav_and_footer_link_to_careers(self):
        html = self.client.get("/careers/").content.decode()
        self.assertRegex(html, r'<a href="/careers/"\s+class="active-link">\s*Careers')
        self.assertIn('<li><a href="/careers/"><i class="fa-solid fa-briefcase"></i> Careers</a></li>', html)
        footer = html.split('<footer class="footer"')[1]
        self.assertIn('<a href="/careers/">Careers</a>', footer)


class CareersApplicationTests(CareersTestMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.job = make_job()
        self.url = f"/careers/{self.job.slug}/apply/"

    def test_form_page_is_noindex(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")
        html = response.content.decode()
        self.assertIn('<meta name="robots" content="noindex, nofollow">', html)
        self.assertIn("csrfmiddlewaretoken", html)
        self.assertIn("How we use your application", html)
        self.assertNotIn('type="file"', html)

    def test_valid_application_is_saved_and_confirmed(self):
        response = self.client.post(self.url, valid_application())
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        application = JobApplication.objects.get()
        self.assertEqual(application.job, self.job)
        self.assertEqual(application.job_title, self.job.title)
        self.assertEqual(application.status, "new")
        self.assertTrue(application.consent)
        self.assertIn("your application has been received", self.client.get(self.url).content.decode())
        # the confirmation is shown once, then the form returns
        self.assertNotIn("your application has been received", self.client.get(self.url).content.decode())

    def test_applicant_data_never_appears_publicly(self):
        self.client.post(self.url, valid_application())
        for path in ("/careers/", f"/careers/{self.job.slug}/", self.url, "/sitemap.xml"):
            body = Client().get(path).content.decode()
            self.assertNotIn("applicant@example.com", body, path)
            self.assertNotIn("Test Applicant", body, path)

    def test_validation_errors(self):
        cases = {
            "full_name": "",
            "email": "not-an-email",
            "message": "too short",
            "profile_url": "javascript:alert(1)",
            "phone": "call me maybe",
        }
        for field, value in cases.items():
            response = self.client.post(self.url, valid_application(**{field: value}))
            self.assertEqual(response.status_code, 200, field)
            self.assertIn(f'aria-describedby="err_{field}"', response.content.decode().replace(
                f'hint_{field} err_{field}', f'err_{field}'), field)
        data = valid_application()
        del data["consent"]
        response = self.client.post(self.url, data)
        self.assertIn("Please confirm you have read", response.content.decode())
        self.assertEqual(JobApplication.objects.count(), 0)

    def test_tampered_or_missing_timestamp_is_rejected(self):
        response = self.client.post(self.url, valid_application(form_ts="bogus"))
        self.assertIn("This form has expired", response.content.decode())
        self.assertEqual(JobApplication.objects.count(), 0)

    def test_honeypot_and_too_fast_submissions_are_dropped(self):
        response = self.client.post(self.url, valid_application(website="http://spam.example"))
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        JobApplicationForm.MIN_SECONDS = 3
        response = self.client.post(self.url, valid_application(email="fast@example.com"))
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        self.assertEqual(JobApplication.objects.count(), 0)

    def test_duplicate_submission_is_not_saved_twice(self):
        self.client.post(self.url, valid_application())
        self.client.post(self.url, valid_application())
        self.assertEqual(JobApplication.objects.count(), 1)

    def test_rate_limit(self):
        for i in range(5):
            self.client.post(self.url, valid_application(email=f"a{i}@example.com"))
        response = self.client.post(self.url, valid_application(email="a6@example.com"))
        self.assertEqual(response.status_code, 429)
        self.assertEqual(JobApplication.objects.count(), 5)

    def test_csrf_is_required(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(self.url, valid_application())
        self.assertEqual(response.status_code, 403)
        self.assertEqual(JobApplication.objects.count(), 0)

    def test_closed_and_draft_roles_refuse_applications(self):
        self.job.status = JobOpening.STATUS_CLOSED
        self.job.save()
        self.assertEqual(self.client.post(self.url, valid_application()).status_code, 410)
        self.job.status = JobOpening.STATUS_DRAFT
        self.job.save()
        self.assertEqual(self.client.post(self.url, valid_application()).status_code, 404)
        self.assertEqual(JobApplication.objects.count(), 0)


class CareersAdminTests(CareersTestMixin, TestCase):

    ADMIN_PAGES = (
        "/admin/careers/",
        "/admin/careers/new/",
        "/admin/careers/applications/",
    )

    def test_anonymous_users_cannot_manage_jobs_or_view_applications(self):
        job = make_job()
        application = JobApplication.objects.create(
            job=job, job_title=job.title, full_name="Secret Person", email="secret@example.com",
            message="Private message text.", consent=True)
        paths = self.ADMIN_PAGES + (
            f"/admin/careers/{job.id}/edit/",
            f"/admin/careers/applications/{application.id}/",
        )
        for path in paths:
            response = self.client.get(path)
            self.assertRedirects(response, "/admin/login/", fetch_redirect_response=False, msg_prefix=path)
            self.assertNotIn("secret@example.com", response.content.decode())
        for path, data in (
            (f"/admin/careers/{job.id}/status/", {"action": "close"}),
            (f"/admin/careers/{job.id}/delete/", {}),
            (f"/admin/careers/applications/{application.id}/delete/", {}),
            (f"/admin/careers/applications/{application.id}/", {"status": "hired"}),
            ("/admin/careers/new/", {"title": "Hacked", "summary": "x", "status": "published"}),
        ):
            response = self.client.post(path, data)
            self.assertRedirects(response, "/admin/login/", fetch_redirect_response=False, msg_prefix=path)
        job.refresh_from_db()
        application.refresh_from_db()
        self.assertEqual(job.status, JobOpening.STATUS_PUBLISHED)
        self.assertEqual(application.status, "new")
        self.assertEqual(JobOpening.objects.count(), 1)

    def test_admin_pages_render_and_are_noindex(self):
        self.login_admin()
        job = make_job()
        for path in self.ADMIN_PAGES + (f"/admin/careers/{job.id}/edit/",):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")

    def test_admin_create_edit_publish_unpublish_close_delete(self):
        self.login_admin()
        public = Client()
        response = self.client.post("/admin/careers/new/", {
            "title": "QA Engineer",
            "slug": "",
            "status": "draft",
            "summary": "Test web and mobile applications before release.",
            "display_order": 0,
        })
        self.assertRedirects(response, "/admin/careers/")
        job = JobOpening.objects.get()
        self.assertEqual(job.slug, "qa-engineer")
        self.assertEqual(self.client.get("/careers/qa-engineer/").status_code, 200)  # admin preview
        self.assertEqual(public.get("/careers/qa-engineer/").status_code, 404)
        self.assertNotIn("QA Engineer", main_html(public.get("/careers/").content.decode()))

        response = self.client.post(f"/admin/careers/{job.id}/edit/", {
            "title": "QA Engineer", "slug": "qa-engineer", "status": "draft",
            "summary": "Updated summary for the QA role.", "display_order": 3, "department": "Quality",
        })
        self.assertRedirects(response, "/admin/careers/")
        job.refresh_from_db()
        self.assertEqual(job.department, "Quality")

        self.client.post(f"/admin/careers/{job.id}/status/", {"action": "publish"})
        job.refresh_from_db()
        self.assertEqual(job.status, "published")
        self.assertIsNotNone(job.published_at)
        self.assertIn("QA Engineer", main_html(public.get("/careers/").content.decode()))

        self.client.post(f"/admin/careers/{job.id}/status/", {"action": "unpublish"})
        job.refresh_from_db()
        self.assertEqual(job.status, "draft")
        self.assertEqual(public.get("/careers/qa-engineer/").status_code, 404)

        self.client.post(f"/admin/careers/{job.id}/status/", {"action": "close"})
        job.refresh_from_db()
        self.assertEqual(job.status, "closed")
        self.assertEqual(public.get("/careers/qa-engineer/").status_code, 410)

        JobApplication.objects.create(job=job, job_title=job.title, full_name="A", email="a@example.com",
                                      message="Message long enough to count.", consent=True)
        self.client.post(f"/admin/careers/{job.id}/delete/")
        self.assertFalse(JobOpening.objects.exists())
        self.assertEqual(JobApplication.objects.get().job_title, "QA Engineer")
        self.assertEqual(public.get("/careers/qa-engineer/").status_code, 404)

    def test_invalid_job_form_shows_errors(self):
        self.login_admin()
        response = self.client.post("/admin/careers/new/", {"title": "", "summary": "", "status": "draft"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(JobOpening.objects.exists())

    def test_state_changes_require_post(self):
        self.login_admin()
        job = make_job()
        self.assertEqual(self.client.get(f"/admin/careers/{job.id}/status/?action=close").status_code, 405)
        self.assertEqual(self.client.get(f"/admin/careers/{job.id}/delete/").status_code, 405)
        job.refresh_from_db()
        self.assertEqual(job.status, "published")

    def test_duplicate_slug_gets_suffix(self):
        self.login_admin()
        make_job()
        self.client.post("/admin/careers/new/", {
            "title": "Python Developer", "slug": "", "status": "draft",
            "summary": "Second opening with the same title.", "display_order": 0,
        })
        self.assertTrue(JobOpening.objects.filter(slug="python-developer-2").exists())

    def test_admin_reviews_and_deletes_application(self):
        self.login_admin()
        job = make_job()
        application = JobApplication.objects.create(
            job=job, job_title=job.title, full_name="Applicant One", email="one@example.com",
            message="I would like to apply for this role.", consent=True)
        self.assertIn("Applicant One", self.client.get("/admin/careers/applications/").content.decode())
        detail = f"/admin/careers/applications/{application.id}/"
        self.assertIn("one@example.com", self.client.get(detail).content.decode())
        self.client.post(detail, {"status": "shortlisted", "internal_notes": "Call next week"})
        application.refresh_from_db()
        self.assertEqual(application.status, "shortlisted")
        self.client.post(f"{detail}delete/")
        self.assertFalse(JobApplication.objects.exists())

    def test_dashboard_links_to_careers(self):
        self.login_admin()
        html = self.client.get("/admin/dashboard/").content.decode()
        self.assertIn('href="/admin/careers/"', html)


class CareersCrawlTests(CareersTestMixin, TestCase):

    def test_sitemap_lists_careers_and_open_roles_only(self):
        make_job(slug="open-role")
        make_job(slug="draft-role", status=JobOpening.STATUS_DRAFT)
        make_job(slug="closed-role", status=JobOpening.STATUS_CLOSED)
        make_job(slug="expired-role", closing_date=timezone.localdate() - datetime.timedelta(days=1))
        body = self.client.get("/sitemap.xml").content.decode()
        self.assertIn("/careers/</loc>", body)
        self.assertIn("/careers/open-role/</loc>", body)
        for slug in ("draft-role", "closed-role", "expired-role"):
            self.assertNotIn(slug, body)
        self.assertNotIn("/apply/", body)
        self.assertNotIn("/admin/", body)

    def test_robots_keeps_careers_crawlable_and_admin_blocked(self):
        body = self.client.get("/robots.txt").content.decode()
        self.assertIn("Disallow: /admin/", body)
        self.assertNotIn("Disallow: /careers", body)


# --- Ubersuggest audit fixes (title length, thin content, /blog/ keywords) ---

AUDIT_TITLES = {
    "/locations/visakhapatnam/": "Software Development Company in Visakhapatnam | KK Digital Growth",
    "/services/custom-software-development/": "Custom Software Development Services | KK Digital Growth",
    "/services/erp-development/": "ERP Development Services | KK Digital Growth",
    "/services/mobile-app-development/": "Mobile App Development Services | KK Digital Growth",
    "/services/web-development/": "Web Development Services | KK Digital Growth",
    "/blog/": "Software & Web Development Blog | KK Digital Growth",
    "/case-studies/": "Case Studies: Web, App & ERP Projects | KK Digital Growth",
    "/contact/": "Contact KK Digital Growth | Software Company in Visakhapatnam",
}


def visible_words(html):
    """Words in the page body between the header and the footer (what the audit counts as content)."""
    body = html.split("</header>", 1)[-1].split('<footer class="footer"', 1)[0]
    body = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", body, flags=re.S)
    body = re.sub(r'<div class="mobile-menu".*?</nav>\s*</div>', " ", body, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", body)
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'&.-]*", text))


class AuditFixTests(SimpleTestCase):

    def get_html(self, path):
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200, path)
        return response.content.decode()

    def test_titles_are_short_unique_and_server_rendered_once(self):
        seen = set()
        for path, expected in AUDIT_TITLES.items():
            html = self.get_html(path)
            titles = re.findall(r"<title>(.*?)</title>", html, re.S)
            self.assertEqual(len(titles), 1, path)
            title = unescape(titles[0].strip())
            self.assertEqual(title, expected, path)
            self.assertLessEqual(len(title), 65, path)
            self.assertNotIn(title, seen, path)
            seen.add(title)
            og = re.search(r'<meta property="og:title" content="([^"]*)">', html).group(1)
            twitter = re.search(r'<meta name="twitter:title" content="([^"]*)">', html).group(1)
            self.assertEqual(unescape(og), expected, path)
            self.assertEqual(unescape(twitter), expected, path)
            self.assertIn(f'<link rel="canonical" href="{SITE}{path}">', html)
            self.assertEqual(len(re.findall(r"<h1[\s>]", html)), 1, path)
            self.assertRegex(html, r'<meta name="description" content="[^"]{70,}">')

    def test_blog_url_title_and_heading_share_keywords(self):
        self.assertEqual(reverse("public_blog_list"), "/blog/")
        html = self.get_html("/blog/")
        title = re.search(r"<title>(.*?)</title>", html).group(1)
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S).group(1)
        description = re.search(r'<meta name="description" content="([^"]+)"', html).group(1)
        for text in (title, h1, description):
            self.assertIn("blog", text.lower())
        self.assertIn("software", title.lower())
        self.assertIn("web development", unescape(title).lower())

    def test_thin_pages_have_substantial_content(self):
        for path, minimum in (("/blog/", 450), ("/case-studies/", 600), ("/contact/", 450)):
            words = visible_words(self.get_html(path))
            self.assertGreaterEqual(words, minimum, f"{path} has {words} words")

    def test_new_content_links_resolve(self):
        for path in ("/blog/", "/case-studies/", "/contact/"):
            html = self.get_html(path)
            sections = "".join(re.findall(r'<section class="kk-cb-section.*?</section>', html, re.S))
            self.assertTrue(sections, path)
            for href in set(re.findall(r'href="(/[^"#?]*)"', sections)):
                if href == "/careers/":
                    continue
                self.assertEqual(self.client.get(href).status_code, 200, f"{path} -> {href}")

class TechStackSectionTests(SimpleTestCase):
    """Clients page: "Platforms & Technologies We Use" replaced the WordPress/Shopify block."""

    def test_section_cards_and_badges(self):
        html = self.client.get("/clients/").content.decode()
        section = re.search(r'<section class="ts-section".*?</section>', html, re.S).group(0)
        self.assertIn("Our technology stack", section)
        self.assertIn("Platforms &amp; Technologies <span>We Use</span>", section)
        self.assertEqual(section.count('<article class="ts-card'), 6)
        for name in ("JavaScript", "React.js", "Node.js", "Django", "PostgreSQL", "Docker", "OpenAI"):
            self.assertIn(f"<span>{name}</span>", section)
        self.assertNotIn("WordPress", section)
        self.assertNotIn("Shopify", section)
        self.assertNotIn("platforms-section", html)
        # every logo referenced in the section exists in the inline sprite
        for icon in set(re.findall(r'<use href="#(ts-[a-z]+)"', section)):
            self.assertIn(f'<symbol id="{icon}"', html)
        for href in set(re.findall(r'class="ts-chevron" href="([^"]+)"', section)):
            self.assertEqual(self.client.get(href).status_code, 200, href)
        self.assertIn("fonts.googleapis.com/css2?family=Plus+Jakarta+Sans", html)
