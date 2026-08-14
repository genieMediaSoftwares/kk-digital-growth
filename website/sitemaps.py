from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.8

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
        ]

    def location(self, item):
        return reverse(item)

class CaseStudySitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.8

    def items(self):
        from .views import CASE_STUDIES_DATA
        return list(CASE_STUDIES_DATA.keys())

    def location(self, item):
        return reverse('case_study_detail', kwargs={'slug': item})
