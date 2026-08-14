from django.conf import settings
from django.urls import path
from django.views.generic import RedirectView, TemplateView
from django.views.static import serve as serve_media
from django.contrib.sitemaps.views import sitemap
from website.sitemaps import StaticViewSitemap, CaseStudySitemap
from website import views

sitemaps = {
    'static': StaticViewSitemap,
    'case_studies': CaseStudySitemap,
}

urlpatterns = [
    path('', views.home, name='home'),
    path('consultation/', views.consultation, name='consultation'),
    path('services/', views.services, name='services'),
    path('process/', views.process, name='process'),
    path("clients/", views.clients, name="clients"),
    path('contact/', views.contact, name='contact'),
    path("about/", views.about, name="about"),
    path('case-studies/', views.case_studies, name='case_studies'),
    path('case-studies/<slug:slug>/', views.case_study_detail, name='case_study_detail'),
    
    # Custom Admin Routes
    path('admin/login/', views.admin_login_view, name='admin_login'),
    path('admin/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin/logout/', views.admin_logout_view, name='admin_logout'),
    path('admin/', views.admin_login_view),

    # Blog Management CMS Routes
    path('blog/admin/', views.blog_dashboard_view, name='blog_dashboard'),
    path('blog/new/', views.blog_create_view, name='blog_create'),
    path('blog/edit/<int:blog_id>/', views.blog_edit_view, name='blog_edit'),
    path('blog/delete/<int:blog_id>/', views.blog_delete_view, name='blog_delete'),
    path('blog/publish/<int:blog_id>/', views.blog_toggle_status_view, {'new_status': 'published'}, name='blog_publish'),
    path('blog/draft/<int:blog_id>/', views.blog_toggle_status_view, {'new_status': 'draft'}, name='blog_draft'),

    # Public Blog Routes
    path('blog/', views.public_blog_list_view, name='public_blog_list'),
    path('blog/<path:slug>/', views.public_blog_detail_view, name='public_blog_detail'),

    # Blog images stored by Django. Matches the /uploads/<file> path Hostinger
    # serves, so image URLs already in blogs.image resolve either way.
    path('uploads/<path:path>', serve_media, {'document_root': settings.MEDIA_ROOT}, name='uploaded_image'),

    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain'), name='robots_txt'),
    path('favicon.ico', RedirectView.as_view(url='/static/images/kk-logo.png')),
]
