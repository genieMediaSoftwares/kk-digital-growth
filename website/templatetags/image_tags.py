from django import template
from django.templatetags.static import static
from django.utils.html import format_html

register = template.Library()

# Original static path -> (WebP thumbnail, PNG fallback thumbnail, width, height).
# Thumbnails are 144px tall (3x the ~48px testimonial logo box) and keep the
# original aspect ratio, so object-fit: cover crops the same area as before.
TESTIMONIAL_THUMBS = {
    "images/meerabasu-home.png": ("images/opt/meerabasu-home-thumb.webp", "images/opt/meerabasu-home-thumb.png", 307, 144),
    "images/kns-metal.png": ("images/opt/kns-metal-thumb.webp", "images/opt/kns-metal-thumb.png", 302, 144),
    "images/laserfold.png": ("images/opt/laserfold-thumb.webp", "images/opt/laserfold-thumb.png", 312, 144),
    "images/geniestudio.png": ("images/opt/geniestudio-thumb.webp", "images/opt/geniestudio-thumb.png", 298, 144),
    "images/buildzon.png": ("images/opt/buildzon-thumb.webp", "images/opt/buildzon-thumb.png", 299, 144),
    "images/nucon.png": ("images/opt/nucon-thumb.webp", "images/opt/nucon-thumb.png", 302, 144),
    "images/synergene.png": ("images/opt/synergene-thumb.webp", "images/opt/synergene-thumb.png", 303, 144),
    "images/vivodyne.png": ("images/opt/vivodyne-thumb.webp", "images/opt/vivodyne-thumb.png", 303, 144),
    "images/decagon.png": ("images/opt/decagon-thumb.webp", "images/opt/decagon-thumb.png", 297, 144),
    "images/freenome.png": ("images/opt/freenome-thumb.webp", "images/opt/freenome-thumb.png", 300, 144),
    "images/naren.png": ("images/opt/naren-thumb.webp", "images/opt/naren-thumb.png", 299, 144),
}


@register.simple_tag
def testimonial_thumb(path, alt, css_class):
    """Render a testimonial logo as a WebP thumbnail with a PNG fallback.

    The <picture> uses display:contents so it creates no box of its own and the
    <img> keeps its existing parent, class and CSS sizing. Paths without a
    thumbnail fall back to the original <img> markup unchanged.
    """
    thumb = TESTIMONIAL_THUMBS.get(path)
    if thumb is None:
        return format_html('<img src="{}" alt="{}" class="{}">', static(path), alt, css_class)
    webp, png, width, height = thumb
    return format_html(
        '<picture style="display:contents">'
        '<source srcset="{}" type="image/webp">'
        '<img src="{}" alt="{}" class="{}" width="{}" height="{}">'
        "</picture>",
        static(webp), static(png), alt, css_class, width, height,
    )
