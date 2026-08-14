import os
from datetime import datetime
from django.db import models
from django.conf import settings


class Consultation(models.Model):

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    company_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    project_name = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.first_name


class Contact(models.Model):

    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    service = models.CharField(max_length=100)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


class Admin(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    last_login = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'admins'
        managed = False

    def __str__(self):
        return self.email


class Category(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True)

    class Meta:
        db_table = 'categories'
        managed = False

    def __str__(self):
        return self.name


class Blog(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    permalink = models.CharField(max_length=255, unique=True)
    metaDescription = models.TextField(blank=True, null=True, db_column='metaDescription')
    description = models.TextField()
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='category_id',
        related_name='blogs'
    )
    image = models.CharField(max_length=500, blank=True, null=True)
    keywords = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, default='draft')
    created_at = models.BigIntegerField(blank=True, null=True, db_column='createdAt')
    updated_at = models.BigIntegerField(blank=True, null=True, db_column='updatedAt')

    class Meta:
        db_table = 'blogs'
        managed = False

    def __str__(self):
        return self.title

    @property
    def public_image_url(self):
        """Returns complete HTTPS URL stored in database"""
        if self.image:
            img_str = str(self.image).strip()
            if img_str.startswith('http://') or img_str.startswith('https://'):
                return img_str
            domain = getattr(settings, 'SITE_DOMAIN', 'https://kkdigitalgrowth.com').rstrip('/')
            clean_path = img_str.lstrip('/')
            if clean_path.startswith('uploads/'):
                return f"{domain}/{clean_path}"
            return f"{domain}/uploads/{clean_path}"
        return ""

    @property
    def display_image(self):
        """Returns stored HTTPS public URL for image rendering"""
        return self.public_image_url

    @property
    def created_datetime(self):
        if self.created_at:
            try:
                ts = self.created_at / 1000 if self.created_at > 10000000000 else self.created_at
                return datetime.fromtimestamp(ts)
            except Exception:
                return None
        return None

    @property
    def updated_datetime(self):
        if self.updated_at:
            try:
                ts = self.updated_at / 1000 if self.updated_at > 10000000000 else self.updated_at
                return datetime.fromtimestamp(ts)
            except Exception:
                return None
        return None

    @property
    def get_absolute_url(self):
        """Returns clean detail page URL for blog card navigation"""
        if self.permalink:
            p = str(self.permalink).strip()
            if p.startswith('/blog/'):
                return p
            if p.startswith('/'):
                return f"/blog{p}"
            return f"/blog/{p}"
        return f"/blog/{self.id}/"