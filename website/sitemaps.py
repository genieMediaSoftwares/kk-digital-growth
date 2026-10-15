from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.8
    protocol = "https"

    def items(self):
        return [
            'home',
            'about',
            'services',
            'service_web_development',
            'service_mobile_app_development',
            'service_custom_software',
            'service_erp_development',
            'service_ui_ux_design',
            'service_software_engineering',
            'service_enterprise_systems',
            'service_ai_solutions',
            'service_product_design',
            'service_cloud_devops',
            'service_digital_marketing',
            'service_seo',
            'location_visakhapatnam',
            'process',
            'clients',
            'contact',
            'consultation',
            'case_studies',
            'public_blog_list',
            'careers',
        ]

    def location(self, item):
        return reverse(item)


class CaseStudySitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.8
    protocol = "https"

    def items(self):
        from .views import CASE_STUDIES_DATA
        return list(CASE_STUDIES_DATA.keys())

    def location(self, item):
        return reverse('case_study_detail', kwargs={'slug': item})


class BlogSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7
    protocol = "https"

    def items(self):
        try:
            from .models import Blog
            return list(Blog.objects.filter(status='published'))
        except Exception:
            return []

    def location(self, item):
        return reverse('public_blog_detail', kwargs={'slug': item.permalink})


class JobOpeningSitemap(Sitemap):
    """Open roles only: drafts, closed/expired roles and apply pages are never listed."""
    changefreq = "weekly"
    priority = 0.6
    protocol = "https"

    def items(self):
        try:
            from .models import JobOpening
            return list(JobOpening.objects.open())
        except Exception:
            return []

    def location(self, item):
        return item.get_absolute_url()

    def lastmod(self, item):
        return item.updated_at
