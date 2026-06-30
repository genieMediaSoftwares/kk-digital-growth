from django.contrib import admin
from .models import Consultation, Contact


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = (
        'first_name',
        'last_name',
        'company_name',
        'email',
        'phone_number',
        'created_at'
    )
    search_fields = ('first_name', 'company_name', 'email')


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'email',
        'phone',
        'service',
        'created_at'
    )
    search_fields = ('full_name', 'email')