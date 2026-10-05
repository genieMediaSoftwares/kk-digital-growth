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
            'process',
            'clients',
            'contact',
            'consultation',
            'case_studies',
            'public_blog_list',
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
