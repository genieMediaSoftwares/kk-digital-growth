from django.urls import path
from . import views

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
]
