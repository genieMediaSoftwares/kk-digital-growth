from django.conf import settings
from django.urls import path
from django.views.generic import RedirectView, TemplateView
from django.views.static import serve as serve_media
from django.contrib.sitemaps.views import sitemap
from website.sitemaps import StaticViewSitemap, CaseStudySitemap, BlogSitemap, JobOpeningSitemap
from website import views, careers_views

sitemaps = {
    'static': StaticViewSitemap,
    'case_studies': CaseStudySitemap,
    'blogs': BlogSitemap,
    'careers': JobOpeningSitemap,
}

urlpatterns = [
    path('', views.home, name='home'),
    path('consultation/', views.consultation, name='consultation'),
    path('services/', views.services, name='services'),
    path('services/web-development/', views.service_web_development, name='service_web_development'),
    path('services/mobile-app-development/', views.service_mobile_app_development, name='service_mobile_app_development'),
    path('services/custom-software-development/', views.service_custom_software, name='service_custom_software'),
    path('services/erp-development/', views.service_erp_development, name='service_erp_development'),
    path('services/ui-ux-design/', views.service_ui_ux_design, name='service_ui_ux_design'),
    # Service category landing pages (linked from the Services mega-menu and /services/)
    path('services/software-engineering/', views.service_software_engineering, name='service_software_engineering'),
    path('services/enterprise-business-systems/', views.service_enterprise_systems, name='service_enterprise_systems'),
    path('services/ai-solutions/', views.service_ai_solutions, name='service_ai_solutions'),
    path('services/experience-product-design/', views.service_product_design, name='service_product_design'),
    path('services/cloud-devops/', views.service_cloud_devops, name='service_cloud_devops'),
    path('services/digital-marketing/', views.service_digital_marketing, name='service_digital_marketing'),
    path('services/seo-services/', views.service_seo, name='service_seo'),
    path('locations/visakhapatnam/', views.location_visakhapatnam, name='location_visakhapatnam'),
    path('process/', views.process, name='process'),
    path("clients/", views.clients, name="clients"),
    path('contact/', views.contact, name='contact'),
    path("about/", views.about, name="about"),
    path('case-studies/', views.case_studies, name='case_studies'),
    path('case-studies/<slug:slug>/', views.case_study_detail, name='case_study_detail'),
    path('careers/', careers_views.careers, name='careers'),
    path('careers/<slug:slug>/', careers_views.career_detail, name='career_detail'),
    path('careers/<slug:slug>/apply/', careers_views.career_apply, name='career_apply'),
    
    # Custom Admin Routes
    path('admin/login/', views.admin_login_view, name='admin_login'),
    path('admin/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin/logout/', views.admin_logout_view, name='admin_logout'),
    path('admin/', views.admin_login_view),

    # Careers management (custom admin)
    path('admin/careers/', careers_views.careers_admin_list, name='careers_admin_list'),
    path('admin/careers/new/', careers_views.careers_admin_edit, name='careers_admin_create'),
    path('admin/careers/<int:job_id>/edit/', careers_views.careers_admin_edit, name='careers_admin_edit'),
    path('admin/careers/<int:job_id>/status/', careers_views.careers_admin_status, name='careers_admin_status'),
    path('admin/careers/<int:job_id>/delete/', careers_views.careers_admin_delete, name='careers_admin_delete'),
    path('admin/careers/applications/', careers_views.careers_admin_applications, name='careers_admin_applications'),
    path('admin/careers/applications/<int:application_id>/', careers_views.careers_admin_application_detail, name='careers_admin_application_detail'),
    path('admin/careers/applications/<int:application_id>/delete/', careers_views.careers_admin_application_delete, name='careers_admin_application_delete'),

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
    path('llms.txt', TemplateView.as_view(template_name='llms.txt', content_type='text/plain; charset=utf-8'), name='llms_txt'),
    path('favicon.ico', RedirectView.as_view(url='/static/images/opt/favicon-48.png')),
]
