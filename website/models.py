import os
from datetime import datetime
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone


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

# --- Careers ---

class JobOpeningQuerySet(models.QuerySet):

    def open(self):
        """Published roles whose closing date (if any) has not passed."""
        today = timezone.localdate()
        return self.filter(status=JobOpening.STATUS_PUBLISHED).filter(
            models.Q(closing_date__isnull=True) | models.Q(closing_date__gte=today)
        )


class JobOpening(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_PUBLISHED = 'published'
    STATUS_CLOSED = 'closed'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PUBLISHED, 'Published'),
        (STATUS_CLOSED, 'Closed'),
    ]

    WORK_MODE_CHOICES = [
        ('on_site', 'On-site'),
        ('hybrid', 'Hybrid'),
        ('remote', 'Remote'),
    ]

    # Values are schema.org JobPosting employmentType codes.
    EMPLOYMENT_TYPE_CHOICES = [
        ('FULL_TIME', 'Full-time'),
        ('PART_TIME', 'Part-time'),
        ('CONTRACTOR', 'Contract'),
        ('INTERN', 'Internship'),
        ('TEMPORARY', 'Temporary'),
    ]

    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, help_text="Used in the URL: /careers/<slug>/")
    department = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=150, blank=True, help_text="Leave blank unless confirmed, e.g. Visakhapatnam, Andhra Pradesh")
    work_mode = models.CharField(max_length=20, choices=WORK_MODE_CHOICES, blank=True)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, blank=True)
    summary = models.CharField(max_length=300, help_text="One or two sentences shown on the Careers page card.")
    description = models.TextField(blank=True, help_text="Full description. Separate paragraphs with a blank line.")
    responsibilities = models.TextField(blank=True, help_text="One item per line.")
    required_skills = models.TextField(blank=True, help_text="One item per line.")
    preferred_skills = models.TextField(blank=True, help_text="One item per line.")
    application_instructions = models.TextField(blank=True, help_text="Shown above the application form.")
    closing_date = models.DateField(blank=True, null=True, help_text="Last day to apply. The role stops showing after this date.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT, db_index=True)
    display_order = models.PositiveIntegerField(default=0, help_text="Lower numbers are listed first.")
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = JobOpeningQuerySet.as_manager()

    class Meta:
        ordering = ['display_order', '-published_at', '-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.status == self.STATUS_PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('career_detail', kwargs={'slug': self.slug})

    @property
    def is_open(self):
        if self.status != self.STATUS_PUBLISHED:
            return False
        return self.closing_date is None or self.closing_date >= timezone.localdate()

    @staticmethod
    def _lines(text):
        items = []
        for line in (text or '').splitlines():
            line = line.strip().lstrip('-*\u2022').strip()
            if line:
                items.append(line)
        return items

    @property
    def description_paragraphs(self):
        text = (self.description or '').replace('\r\n', '\n')
        return [p.strip() for p in text.split('\n\n') if p.strip()]

    @property
    def responsibilities_list(self):
        return self._lines(self.responsibilities)

    @property
    def required_skills_list(self):
        return self._lines(self.required_skills)

    @property
    def preferred_skills_list(self):
        return self._lines(self.preferred_skills)


class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('reviewing', 'Reviewing'),
        ('shortlisted', 'Shortlisted'),
        ('rejected', 'Rejected'),
        ('hired', 'Hired'),
    ]

    # SET_NULL keeps applications if a job is deleted; job_title records what was applied for.
    job = models.ForeignKey(JobOpening, on_delete=models.SET_NULL, null=True, blank=True, related_name='applications')
    job_title = models.CharField(max_length=150)
    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    profile_url = models.URLField(max_length=300, blank=True)
    message = models.TextField()
    consent = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', db_index=True)
    internal_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} - {self.job_title}"
