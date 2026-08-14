import os
from django import forms
from .models import Contact, Category, Blog


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