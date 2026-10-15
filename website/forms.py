import os
import re
import time

from django import forms
from django.core import signing
from django.utils.text import slugify
from .models import Contact, Category, Blog, JobOpening, JobApplication


class ContactForm(forms.ModelForm):

    class Meta:

        model = Contact

        fields = '__all__'


class AdminLoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address',
            'id': 'admin-email',
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password',
            'id': 'admin-password',
            'autocomplete': 'current-password'
        })
    )


class BlogForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'blog-category-select'})
    )
    image_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control d-none', 'id': 'blog-image-input', 'accept': 'image/jpeg,image/png,image/webp,image/gif'})
    )

    class Meta:
        model = Blog
        fields = ['title', 'permalink', 'metaDescription', 'description', 'category', 'image', 'keywords', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Blog Title...', 'id': 'blog-title'}),
            'permalink': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. /blog/technology/ai-healthcare', 'id': 'blog-permalink'}),
            'metaDescription': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter meta description (max 160 characters)...', 'id': 'blog-meta-desc', 'maxlength': '160'}),
            'description': forms.HiddenInput(attrs={'id': 'blog-description'}),
            'keywords': forms.HiddenInput(attrs={'id': 'blog-keywords'}),
            'status': forms.HiddenInput(attrs={'id': 'blog-status', 'value': 'draft'}),
            'image': forms.TextInput(attrs={'class': 'form-control mt-2', 'placeholder': 'Paste Image URL (e.g. https://geniestudio.in/uploads/...)', 'id': 'blog-image-url-input'}),
        }

    def clean_image_file(self):
        img_file = self.cleaned_data.get('image_file')
        if img_file and hasattr(img_file, 'name'):
            if img_file.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Featured image size must be less than 5MB.")
            ext = os.path.splitext(img_file.name)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
                raise forms.ValidationError("Only JPG, JPEG, PNG, WebP and GIF image formats are allowed.")
        return img_file

    def clean_metaDescription(self):
        meta_desc = self.cleaned_data.get('metaDescription')
        if meta_desc and len(meta_desc) > 160:
            raise forms.ValidationError("Meta description must not exceed 160 characters.")
        return meta_desc


# --- Careers ---

class JobOpeningForm(forms.ModelForm):
    """Admin form for creating and editing job openings."""

    class Meta:
        model = JobOpening
        fields = [
            'title', 'slug', 'status', 'department', 'location', 'work_mode', 'employment_type',
            'summary', 'description', 'responsibilities', 'required_skills', 'preferred_skills',
            'application_instructions', 'closing_date', 'display_order',
        ]
        widgets = {
            'summary': forms.Textarea(attrs={'rows': 2, 'maxlength': 300}),
            'description': forms.Textarea(attrs={'rows': 6}),
            'responsibilities': forms.Textarea(attrs={'rows': 5}),
            'required_skills': forms.Textarea(attrs={'rows': 5}),
            'preferred_skills': forms.Textarea(attrs={'rows': 4}),
            'application_instructions': forms.Textarea(attrs={'rows': 3}),
            'closing_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].required = False
        self.fields['slug'].help_text = "Optional. Generated from the title if left blank."
        for name, field in self.fields.items():
            css = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs.setdefault('class', css)

    def clean_slug(self):
        slug = slugify(self.cleaned_data.get('slug') or self.cleaned_data.get('title') or '')
        if not slug:
            # clean_slug runs after clean_title, so fall back to the submitted title
            slug = slugify(self.data.get('title', ''))
        if not slug:
            raise forms.ValidationError("Enter a title or slug.")
        base, n = slug[:160], 2
        qs = JobOpening.objects.exclude(pk=self.instance.pk)
        while qs.filter(slug=slug).exists():
            slug = f"{base}-{n}"
            n += 1
        return slug


class JobApplicationForm(forms.Form):
    """Public application form. No file upload: the site has no private file storage."""

    MIN_SECONDS = 3
    MAX_AGE_SECONDS = 60 * 60 * 6

    full_name = forms.CharField(max_length=120)
    email = forms.EmailField(max_length=254)
    phone = forms.CharField(max_length=20, required=False)
    profile_url = forms.URLField(max_length=300, required=False, assume_scheme='https')
    message = forms.CharField(max_length=4000, widget=forms.Textarea)
    consent = forms.BooleanField(required=True, error_messages={
        'required': "Please confirm you have read how we use your application details.",
    })
    # Spam protection: a hidden field people leave empty, and a signed render time.
    website = forms.CharField(required=False)
    form_ts = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial['form_ts'] = signing.TimestampSigner(salt='careers-apply').sign('ok')

    def clean_full_name(self):
        name = self.cleaned_data['full_name'].strip()
        if len(name) < 2:
            raise forms.ValidationError("Please enter your full name.")
        return name

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if phone and not re.fullmatch(r'\+?[0-9 ()-]{7,20}', phone):
            raise forms.ValidationError("Enter a valid phone number (digits, spaces, + and - only).")
        return phone

    def clean_message(self):
        message = self.cleaned_data['message'].strip()
        if len(message) < 20:
            raise forms.ValidationError("Please tell us a little more (at least 20 characters).")
        return message

    def clean(self):
        cleaned = super().clean()
        self.is_spam = bool(cleaned.get('website'))
        try:
            signing.TimestampSigner(salt='careers-apply').unsign(
                cleaned.get('form_ts') or '', max_age=self.MAX_AGE_SECONDS)
            age = time.time() - signing.b62_decode(
                (cleaned.get('form_ts') or '').split(':')[-2])
            if age < self.MIN_SECONDS:
                self.is_spam = True
        except (signing.BadSignature, ValueError, IndexError):
            raise forms.ValidationError("This form has expired. Please reload the page and try again.")
        return cleaned


class JobApplicationUpdateForm(forms.ModelForm):
    """Admin form for the review status and internal notes of an application."""

    class Meta:
        model = JobApplication
        fields = ['status', 'internal_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'internal_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
