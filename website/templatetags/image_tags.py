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


# Original static path -> (1x WebP, 2x WebP or None, PNG fallback, width, height).
# 1x is 1000px wide and 2x is 1600px wide (omitted when the original is not wider
# than 1600px); width/height are the real 1x/PNG pixel sizes, same aspect ratio as
# the original, so object-fit: cover crops the same area as before.
CARD_IMAGES = {
    "images/meerabasu-home.png": ("images/opt/meerabasu-home-card.webp", "images/opt/meerabasu-home-card-1600.webp", "images/opt/meerabasu-home-card.png", 1000, 469),
    "images/kns-metal.png": ("images/opt/kns-metal-card.webp", "images/opt/kns-metal-card-1600.webp", "images/opt/kns-metal-card.png", 1000, 477),
    "images/laserfold.png": ("images/opt/laserfold-card.webp", "images/opt/laserfold-card-1600.webp", "images/opt/laserfold-card.png", 1000, 461),
    "images/geniestudio.png": ("images/opt/geniestudio-card.webp", "images/opt/geniestudio-card-1600.webp", "images/opt/geniestudio-card.png", 1000, 483),
    "images/buildzon.png": ("images/opt/buildzon-card.webp", "images/opt/buildzon-card-1600.webp", "images/opt/buildzon-card.png", 1000, 482),
    "images/nucon.png": ("images/opt/nucon-card.webp", "images/opt/nucon-card-1600.webp", "images/opt/nucon-card.png", 1000, 477),
    "images/synergene.png": ("images/opt/synergene-card.webp", "images/opt/synergene-card-1600.webp", "images/opt/synergene-card.png", 1000, 474),
    "images/vivodyne.png": ("images/opt/vivodyne-card.webp", "images/opt/vivodyne-card-1600.webp", "images/opt/vivodyne-card.png", 1000, 476),
    "images/decagon.png": ("images/opt/decagon-card.webp", "images/opt/decagon-card-1600.webp", "images/opt/decagon-card.png", 1000, 485),
    "images/freenome.png": ("images/opt/freenome-card.webp", "images/opt/freenome-card-1600.webp", "images/opt/freenome-card.png", 1000, 479),
    "images/naren.png": ("images/opt/naren-card.webp", None, "images/opt/naren-card.png", 1000, 481),
}


@register.simple_tag
def card_image(path, alt):
    """Render a large screenshot card image as WebP (1x/2x) with a PNG fallback.

    Used for the About success cards and Clients portfolio cards, whose <img>
    has no class of its own. Like testimonial_thumb, the <picture> uses
    display:contents so the <img> keeps its parent box and CSS sizing, and
    paths without a card variant fall back to the original <img> markup.
    """
    card = CARD_IMAGES.get(path)
    if card is None:
        return format_html('<img src="{}" alt="{}">', static(path), alt)
    webp_1x, webp_2x, png, width, height = card
    srcset = f"{static(webp_1x)} 1x, {static(webp_2x)} 2x" if webp_2x else static(webp_1x)
    return format_html(
        '<picture style="display:contents">'
        '<source srcset="{}" type="image/webp">'
        '<img src="{}" alt="{}" width="{}" height="{}">'
        "</picture>",
        srcset, static(png), alt, width, height,
    )
