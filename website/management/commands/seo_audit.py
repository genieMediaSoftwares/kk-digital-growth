"""SEO Audit Management Command for Django.

Audits web pages, meta tags, titles, headings, open graph data, schema markup,
robots.txt, and sitemap.xml to verify SEO readiness and best practices.

Usage:
    python manage.py seo_audit                     # Audit all public pages via internal client
    python manage.py seo_audit --url /services/    # Audit a single path
    python manage.py seo_audit --live https://...  # Audit against a live domain
    python manage.py seo_audit --verbose           # Detailed output for each tag
"""

import json
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

from django.conf import settings
from django.core.management.base import BaseCommand
from django.test import Client


class SEOHtmlParser(HTMLParser):
    """Fast, dependency-free HTML parser for SEO audits."""

    def __init__(self):
        super().__init__()
        self.title = None
        self._in_title = False
        self._title_chunks = []

        self.metas = []
        self.links = []

        self.h1_list = []
        self._in_h1 = False
        self._h1_chunks = []

        self.h2_list = []
        self._in_h2 = False
        self._h2_chunks = []

        self.images = []

        self.json_ld_list = []
        self._in_json_ld = False
        self._json_ld_chunks = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = {k.lower(): (v or "") for k, v in attrs if k}
        tag_lower = tag.lower()

        if tag_lower == 'title':
            self._in_title = True
            self._title_chunks = []
        elif tag_lower == 'meta':
            self.metas.append(attrs_dict)
        elif tag_lower == 'link':
            self.links.append(attrs_dict)
        elif tag_lower == 'h1':
            self._in_h1 = True
            self._h1_chunks = []
        elif tag_lower == 'h2':
            self._in_h2 = True
            self._h2_chunks = []
        elif tag_lower == 'img':
            src = attrs_dict.get('src', '')
            alt = attrs_dict.get('alt', None)
            has_alt = alt is not None and alt.strip() != ""
            self.images.append({
                'src': src,
                'alt': alt or "",
                'has_alt': has_alt,
            })
        elif tag_lower == 'script':
            script_type = attrs_dict.get('type', '').strip().lower()
            if script_type == 'application/ld+json':
                self._in_json_ld = True
                self._json_ld_chunks = []

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower == 'title':
            self._in_title = False
            self.title = "".join(self._title_chunks).strip()
        elif tag_lower == 'h1':
            self._in_h1 = False
            text = "".join(self._h1_chunks).strip()
            if text:
                self.h1_list.append(text)
        elif tag_lower == 'h2':
            self._in_h2 = False
            text = "".join(self._h2_chunks).strip()
            if text:
                self.h2_list.append(text)
        elif tag_lower == 'script':
            if self._in_json_ld:
                self._in_json_ld = False
                raw = "".join(self._json_ld_chunks).strip()
                if raw:
                    self.json_ld_list.append(raw)

    def handle_data(self, data):
        if self._in_title:
            self._title_chunks.append(data)
        if self._in_h1:
            self._h1_chunks.append(data)
        if self._in_h2:
            self._h2_chunks.append(data)
        if self._in_json_ld:
            self._json_ld_chunks.append(data)

    def get_meta(self, name_or_prop):
        target = name_or_prop.lower()
        for m in self.metas:
            if m.get('name', '').lower() == target or m.get('property', '').lower() == target:
                return m.get('content', '')
        return None

    def get_canonical(self):
        for link in self.links:
            if link.get('rel', '').lower() == 'canonical':
                return link.get('href', '')
        return None


class Command(BaseCommand):
    help = "Perform a comprehensive SEO audit of website routes, meta tags, schema, robots, and sitemaps."

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            default=None,
            help="Audit a specific path or URL (e.g., /services/ or /case-studies/)",
        )
        parser.add_argument(
            '--live',
            type=str,
            default=None,
            help="Audit a live website host (e.g., https://kkdigitalgrowth.com)",
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help="Show detailed metadata and schema details for each page",
        )

    def handle(self, *args, **options):
        single_url = options.get('url')
        live_host = options.get('live')
        verbose = options.get('verbose', False)

        if live_host:
            live_host = live_host.rstrip('/')

        self.stdout.write(self.style.MIGRATE_HEADING("=" * 72))
        self.stdout.write(self.style.MIGRATE_HEADING("              KK DIGITAL SEO AUDIT & HEALTH CHECK              "))
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 72))

        mode_str = f"Live Mode ({live_host})" if live_host else "Django Test Client (Internal Fast Mode)"
        self.stdout.write(f"Mode: {mode_str}\n")

        # Ensure test host is permitted in ALLOWED_HOSTS for internal client audit
        if 'testserver' not in settings.ALLOWED_HOSTS:
            try:
                settings.ALLOWED_HOSTS.append('testserver')
            except Exception:
                pass
        if 'localhost' not in settings.ALLOWED_HOSTS:
            try:
                settings.ALLOWED_HOSTS.append('localhost')
            except Exception:
                pass

        # Collect targets
        routes = self._gather_routes(single_url)

        total_pages = 0
        total_checks = 0
        passed_checks = 0
        warning_count = 0
        error_count = 0
        recommendations = []

        client = Client(raise_request_exception=False) if not live_host else None

        for route_info in routes:
            path = route_info['path']
            title = route_info['label']
            route_type = route_info.get('type', 'html')

            self.stdout.write(self.style.SUCCESS(f"\n--- Checking: {title} ({path}) ---"))
            total_pages += 1

            # Fetch content
            status_code, content, elapsed_ms = self._fetch_url(client, live_host, path)

            if status_code != 200:
                self.stdout.write(self.style.ERROR(f"  [X] HTTP Status: {status_code} (Expected 200 OK)"))
                error_count += 1
                total_checks += 1
                recommendations.append(f"Fix broken route or 404/500 error on {path}")
                continue

            self.stdout.write(f"  [OK] HTTP 200 OK (Response: {elapsed_ms:.1f}ms)")
            passed_checks += 1
            total_checks += 1

            if route_type == 'robots':
                p, w, e, recs = self._audit_robots_txt(content)
            elif route_type == 'sitemap':
                p, w, e, recs = self._audit_sitemap_xml(content)
            elif route_type == 'llms':
                p, w, e, recs = self._audit_llms_txt(content)
            else:
                p, w, e, recs = self._audit_html_page(content, path, verbose)

            passed_checks += p
            warning_count += w
            error_count += e
            recommendations.extend(recs)

        # Summary
        self._print_summary(total_pages, total_checks, passed_checks, warning_count, error_count, recommendations)

    def _gather_routes(self, single_url):
        """Build the list of paths to audit."""
        if single_url:
            path = single_url if single_url.startswith('/') else f"/{single_url}"
            route_type = 'html'
            if 'robots.txt' in path:
                route_type = 'robots'
            elif 'sitemap.xml' in path:
                route_type = 'sitemap'
            elif 'llms.txt' in path:
                route_type = 'llms'
            return [{'path': path, 'label': 'Custom Route', 'type': route_type}]

        routes = [
            {'path': '/', 'label': 'Home Page', 'type': 'html'},
            {'path': '/about/', 'label': 'About Page', 'type': 'html'},
            {'path': '/services/', 'label': 'Services Page', 'type': 'html'},
            {'path': '/process/', 'label': 'Process Page', 'type': 'html'},
            {'path': '/clients/', 'label': 'Clients Page', 'type': 'html'},
            {'path': '/contact/', 'label': 'Contact Page', 'type': 'html'},
            {'path': '/consultation/', 'label': 'Consultation Page', 'type': 'html'},
            {'path': '/case-studies/', 'label': 'Case Studies List', 'type': 'html'},
            {'path': '/blog/', 'label': 'Blog List Page', 'type': 'html'},
        ]

        # Dynamic Case Study detail
        try:
            from website.views import CASE_STUDIES_DATA
            if CASE_STUDIES_DATA:
                sample_slug = next(iter(CASE_STUDIES_DATA.keys()))
                routes.append({
                    'path': f"/case-studies/{sample_slug}/",
                    'label': f"Case Study Detail ({sample_slug})",
                    'type': 'html'
                })
        except Exception:
            pass

        # Dynamic Blog detail
        try:
            from website.models import Blog
            sample_blog = Blog.objects.filter(status='published').first()
            if sample_blog and sample_blog.permalink:
                routes.append({
                    'path': f"/blog/{sample_blog.permalink}/",
                    'label': f"Blog Detail ({sample_blog.permalink})",
                    'type': 'html'
                })
        except Exception:
            pass

        # Technical SEO assets
        routes.extend([
            {'path': '/robots.txt', 'label': 'Robots Directives', 'type': 'robots'},
            {'path': '/sitemap.xml', 'label': 'XML Sitemap', 'type': 'sitemap'},
            {'path': '/llms.txt', 'label': 'LLMs AI Text File', 'type': 'llms'},
        ])

        return routes

    def _fetch_url(self, client, live_host, path):
        """Fetch URL using either Django test Client or live HTTP request."""
        start = time.time()
        if live_host:
            full_url = f"{live_host}{path}"
            req = urllib.request.Request(
                full_url,
                headers={'User-Agent': 'KKDigital-SEO-Auditor/1.0'}
            )
            try:
                with urllib.request.urlopen(req, timeout=15) as res:
                    elapsed = (time.time() - start) * 1000
                    return res.status, res.read().decode('utf-8', errors='replace'), elapsed
            except urllib.error.HTTPError as err:
                elapsed = (time.time() - start) * 1000
                return err.code, err.read().decode('utf-8', errors='replace'), elapsed
            except Exception as e:
                elapsed = (time.time() - start) * 1000
                return 500, str(e), elapsed
        else:
            host = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS and settings.ALLOWED_HOSTS[0] != '*' else 'kkdigitalgrowth.com'
            try:
                res = client.get(path, secure=True, HTTP_HOST=host)
                elapsed = (time.time() - start) * 1000
                content = res.content.decode('utf-8', errors='replace') if hasattr(res, 'content') else ''
                return res.status_code, content, elapsed
            except Exception as e:
                elapsed = (time.time() - start) * 1000
                return 500, f"Error rendering {path}: {e}", elapsed

    def _audit_html_page(self, html_content, path, verbose):
        passed = 0
        warnings = 0
        errors = 0
        recs = []

        parser = SEOHtmlParser()
        try:
            parser.feed(html_content)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  [X] Failed to parse HTML: {e}"))
            return 0, 0, 1, [f"Fix HTML malformation on {path}"]

        # 1. Title Tag
        title = parser.title
        if not title:
            self.stdout.write(self.style.ERROR("  [X] Title Tag: MISSING"))
            errors += 1
            recs.append(f"Add a `<title>` tag to {path}")
        else:
            t_len = len(title)
            if 30 <= t_len <= 65:
                self.stdout.write(self.style.SUCCESS(f"  [OK] Title ({t_len} chars): \"{title}\""))
                passed += 1
            elif t_len < 30:
                self.stdout.write(self.style.WARNING(f"  [!] Title ({t_len} chars - Too Short): \"{title}\""))
                warnings += 1
                recs.append(f"Expand `<title>` on {path} to at least 30 characters (currently {t_len})")
            else:
                self.stdout.write(self.style.WARNING(f"  [!] Title ({t_len} chars - May Truncate in Google): \"{title}\""))
                warnings += 1
                recs.append(f"Shorten `<title>` on {path} to under 65 characters (currently {t_len})")

        # 2. Meta Description
        description = parser.get_meta('description')
        if not description:
            self.stdout.write(self.style.ERROR("  [X] Meta Description: MISSING"))
            errors += 1
            recs.append(f"Add `<meta name=\"description\">` tag to {path}")
        else:
            d_len = len(description)
            if 70 <= d_len <= 165:
                self.stdout.write(self.style.SUCCESS(f"  [OK] Meta Description ({d_len} chars): \"{description[:60]}...\""))
                passed += 1
            elif d_len < 70:
                self.stdout.write(self.style.WARNING(f"  [!] Meta Description ({d_len} chars - Too Short): \"{description}\""))
                warnings += 1
                recs.append(f"Expand meta description on {path} to 70-160 characters (currently {d_len})")
            else:
                self.stdout.write(self.style.WARNING(f"  [!] Meta Description ({d_len} chars - May Truncate): \"{description[:60]}...\""))
                warnings += 1
                recs.append(f"Trim meta description on {path} to under 165 characters (currently {d_len})")

        # 3. Canonical Tag
        canonical = parser.get_canonical()
        if not canonical:
            self.stdout.write(self.style.WARNING("  [!] Canonical Link: MISSING"))
            warnings += 1
            recs.append(f"Add `<link rel=\"canonical\" href=\"...\">` to {path}")
        else:
            self.stdout.write(self.style.SUCCESS(f"  [OK] Canonical Link: {canonical}"))
            passed += 1

        # 4. Robots Meta Check
        robots_meta = parser.get_meta('robots')
        if robots_meta:
            if 'noindex' in robots_meta.lower():
                self.stdout.write(self.style.ERROR(f"  [X] Robots Meta: Found 'noindex'! Search engines will ignore this page."))
                errors += 1
                recs.append(f"Remove 'noindex' from robots meta tag on {path}")
            else:
                self.stdout.write(self.style.SUCCESS(f"  [OK] Robots Meta: {robots_meta}"))
                passed += 1

        # 5. Heading Structure (H1 / H2)
        h1_count = len(parser.h1_list)
        if h1_count == 1:
            self.stdout.write(self.style.SUCCESS(f"  [OK] H1 Tag (1): \"{parser.h1_list[0][:70]}\""))
            passed += 1
        elif h1_count == 0:
            self.stdout.write(self.style.ERROR("  [X] H1 Tag: MISSING (Every page must have exactly one <h1>)"))
            errors += 1
            recs.append(f"Add an `<h1>` heading to {path}")
        else:
            self.stdout.write(self.style.WARNING(f"  [!] H1 Tag: Multiple ({h1_count}) found (Best practice is 1 per page)"))
            warnings += 1
            recs.append(f"Keep only one `<h1>` per page on {path} (currently has {h1_count})")

        h2_count = len(parser.h2_list)
        if h2_count > 0:
            self.stdout.write(self.style.SUCCESS(f"  [OK] H2 Subheadings: {h2_count} present"))
            passed += 1
        else:
            self.stdout.write(self.style.WARNING("  [!] H2 Subheadings: None found (H2 tags aid SEO readability)"))
            warnings += 1

        # 6. Open Graph & Social Cards
        og_title = parser.get_meta('og:title')
        og_desc = parser.get_meta('og:description')
        og_image = parser.get_meta('og:image')
        og_url = parser.get_meta('og:url')

        og_score = sum(bool(x) for x in [og_title, og_desc, og_image, og_url])
        if og_score == 4:
            self.stdout.write(self.style.SUCCESS("  [OK] Open Graph Tags: Complete (title, desc, image, url)"))
            passed += 1
        elif og_score > 0:
            missing = []
            if not og_title: missing.append('og:title')
            if not og_desc: missing.append('og:description')
            if not og_image: missing.append('og:image')
            if not og_url: missing.append('og:url')
            self.stdout.write(self.style.WARNING(f"  [!] Open Graph Tags: Partial ({og_score}/4). Missing: {', '.join(missing)}"))
            warnings += 1
            recs.append(f"Complete Open Graph tags ({', '.join(missing)}) on {path}")
        else:
            self.stdout.write(self.style.WARNING("  [!] Open Graph Tags: Missing (Reduces social sharing visibility)"))
            warnings += 1
            recs.append(f"Add Open Graph tags to {path}")

        # 7. Images & Alt Attributes
        total_images = len(parser.images)
        missing_alt = [img['src'] for img in parser.images if not img['has_alt']]
        if total_images == 0:
            if verbose:
                self.stdout.write("  [-] Images: 0 found")
        elif len(missing_alt) == 0:
            self.stdout.write(self.style.SUCCESS(f"  [OK] Image Alt Tags: {total_images}/{total_images} have descriptive alt text"))
            passed += 1
        else:
            self.stdout.write(self.style.WARNING(f"  [!] Image Alt Tags: {len(missing_alt)}/{total_images} missing alt attributes"))
            warnings += 1
            recs.append(f"Add alt attributes to {len(missing_alt)} images on {path}")

        # 8. Structured Data / Schema.org (JSON-LD)
        if parser.json_ld_list:
            schema_types = []
            valid_schemas = 0
            for raw_json in parser.json_ld_list:
                try:
                    data = json.loads(raw_json)
                    valid_schemas += 1
                    if isinstance(data, dict):
                        stype = data.get('@type', 'Unknown')
                        schema_types.append(stype)
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                schema_types.append(item.get('@type', 'Unknown'))
                except json.JSONDecodeError as err:
                    self.stdout.write(self.style.ERROR(f"  [X] Schema JSON-LD: Invalid JSON syntax ({err})"))
                    errors += 1
                    recs.append(f"Fix JSON-LD schema syntax error on {path}")

            if valid_schemas > 0:
                types_str = ", ".join(schema_types) if schema_types else "JSON-LD"
                self.stdout.write(self.style.SUCCESS(f"  [OK] Schema Markup: {valid_schemas} valid block(s) detected ({types_str})"))
                passed += 1
        else:
            if verbose:
                self.stdout.write("  [-] Schema Markup: No JSON-LD blocks found")

        # 9. Mobile Viewport
        viewport = parser.get_meta('viewport')
        if viewport:
            self.stdout.write(self.style.SUCCESS("  [OK] Viewport: Configured for mobile responsiveness"))
            passed += 1
        else:
            self.stdout.write(self.style.ERROR("  [X] Viewport: Missing `<meta name=\"viewport\">` tag"))
            errors += 1
            recs.append(f"Add viewport meta tag to {path}")

        return passed, warnings, errors, recs

    def _audit_robots_txt(self, content):
        passed = 0
        warnings = 0
        errors = 0
        recs = []

        if not content.strip():
            self.stdout.write(self.style.ERROR("  [X] robots.txt is EMPTY"))
            return 0, 0, 1, ["Populate /robots.txt with User-agent and Sitemap directives"]

        has_user_agent = "user-agent:" in content.lower()
        has_sitemap = "sitemap:" in content.lower()
        blocks_all = re.search(r'disallow:\s*/\s*$', content, re.MULTILINE | re.IGNORECASE)

        if has_user_agent:
            self.stdout.write(self.style.SUCCESS("  [OK] User-agent directive defined"))
            passed += 1
        else:
            self.stdout.write(self.style.WARNING("  [!] Missing 'User-agent:' directive"))
            warnings += 1

        if has_sitemap:
            sitemap_match = re.search(r'sitemap:\s*(https?://[^\s]+)', content, re.IGNORECASE)
            loc = sitemap_match.group(1) if sitemap_match else "Configured"
            self.stdout.write(self.style.SUCCESS(f"  [OK] Sitemap Reference: {loc}"))
            passed += 1
        else:
            self.stdout.write(self.style.WARNING("  [!] Missing 'Sitemap:' directive in robots.txt"))
            warnings += 1
            recs.append("Add `Sitemap: https://kkdigitalgrowth.com/sitemap.xml` to /robots.txt")

        if blocks_all:
            self.stdout.write(self.style.ERROR("  [X] CAUTION: 'Disallow: /' detected! Website is blocking all search crawlers!"))
            errors += 1
            recs.append("Remove global 'Disallow: /' block from /robots.txt")

        return passed, warnings, errors, recs

    def _audit_sitemap_xml(self, content):
        passed = 0
        warnings = 0
        errors = 0
        recs = []

        if not content.strip():
            self.stdout.write(self.style.ERROR("  [X] sitemap.xml is EMPTY"))
            return 0, 0, 1, ["Check sitemap generator; sitemap.xml returned 0 bytes"]

        try:
            root = ET.fromstring(content)
            # Handle XML namespace
            namespaces = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            urls = root.findall('ns:url', namespaces) or root.findall('url')
            count = len(urls)

            if count > 0:
                self.stdout.write(self.style.SUCCESS(f"  [OK] Valid XML format with {count} indexed URLs"))
                passed += 1

                # Check if HTTPS is used
                http_count = 0
                for u in urls[:10]:
                    loc = u.find('ns:loc', namespaces) or u.find('loc')
                    if loc is not None and loc.text and loc.text.startswith('http://'):
                        http_count += 1

                if http_count > 0:
                    self.stdout.write(self.style.WARNING("  [!] Non-secure HTTP links detected in sitemap (Should be HTTPS)"))
                    warnings += 1
                    recs.append("Update sitemap protocol to HTTPS")
                else:
                    self.stdout.write(self.style.SUCCESS("  [OK] URLs use HTTPS protocol"))
                    passed += 1
            else:
                self.stdout.write(self.style.WARNING("  [!] Sitemap is valid XML but contains 0 <url> entries"))
                warnings += 1
                recs.append("Add pages to sitemaps.py")
        except ET.ParseError as err:
            self.stdout.write(self.style.ERROR(f"  [X] Invalid XML syntax in sitemap.xml: {err}"))
            errors += 1
            recs.append("Fix XML syntax in /sitemap.xml")

        return passed, warnings, errors, recs

    def _audit_llms_txt(self, content):
        passed = 0
        warnings = 0
        errors = 0
        recs = []

        if content.strip():
            lines = len([l for l in content.splitlines() if l.strip()])
            self.stdout.write(self.style.SUCCESS(f"  [OK] llms.txt available for AI search crawlers ({lines} lines)"))
            passed += 1
        else:
            self.stdout.write(self.style.WARNING("  [!] llms.txt is empty"))
            warnings += 1
        return passed, warnings, errors, recs

    def _print_summary(self, total_pages, total_checks, passed, warnings, errors, recommendations):
        self.stdout.write("\n" + self.style.MIGRATE_HEADING("=" * 72))
        self.stdout.write(self.style.MIGRATE_HEADING("                         AUDIT SUMMARY SCORECARD                        "))
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 72))

        # Calculate score
        all_evals = passed + warnings + (errors * 2)
        score = int(round((passed / max(all_evals, 1)) * 100)) if all_evals else 100

        self.stdout.write(f"Total Routes Audited : {total_pages}")
        self.stdout.write(self.style.SUCCESS(f"Passed Checks        : {passed}"))
        if warnings > 0:
            self.stdout.write(self.style.WARNING(f"Warnings             : {warnings}"))
        else:
            self.stdout.write(f"Warnings             : 0")

        if errors > 0:
            self.stdout.write(self.style.ERROR(f"Errors (Must Fix)    : {errors}"))
        else:
            self.stdout.write(self.style.SUCCESS("Errors (Must Fix)    : 0"))

        score_style = self.style.SUCCESS if score >= 85 else (self.style.WARNING if score >= 60 else self.style.ERROR)
        self.stdout.write(score_style(f"\nOverall SEO Health Score: {score}% / 100%"))

        if recommendations:
            self.stdout.write(self.style.MIGRATE_HEADING("\n--- Recommended Action Items ---"))
            # Deduplicate preserving order
            seen = set()
            idx = 1
            for rec in recommendations:
                if rec not in seen:
                    seen.add(rec)
                    self.stdout.write(f"  {idx}. {rec}")
                    idx += 1
        else:
            self.stdout.write(self.style.SUCCESS("\nOutstanding! All SEO standards and best practices passed without issues."))

        self.stdout.write(self.style.MIGRATE_HEADING("=" * 72) + "\n")
