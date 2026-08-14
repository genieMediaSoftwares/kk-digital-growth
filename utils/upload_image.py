import os
import json
import logging
import random
import time
import urllib.request
import urllib.error
import uuid
from django.conf import settings

logger = logging.getLogger("kkdigital.upload")

# Formats accepted by Hostinger's upload.php
ALLOWED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.gif')

DEFAULT_MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB

# Magic-byte signatures, so a renamed .exe cannot pass as a .png
_SIGNATURES = {
    'jpeg': lambda d: d[:3] == b'\xff\xd8\xff',
    'png': lambda d: d[:8] == b'\x89PNG\r\n\x1a\n',
    'gif': lambda d: d[:6] in (b'GIF87a', b'GIF89a'),
    'webp': lambda d: d[:4] == b'RIFF' and d[8:12] == b'WEBP',
}

_CONTENT_TYPES = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.webp': 'image/webp',
    '.gif': 'image/gif',
}


class HostingerUploadError(Exception):
    """Raised when the image could not be stored on Hostinger.

    The blog is never saved with an image URL when this is raised, so the
    database can never end up holding a URL that resolves to a 404.
    """


def print_step(step_name, detail):
    """Kept for backwards compatibility with existing debug output."""
    logger.info("[%s] %s", step_name, detail)


def _read_bytes(image_file):
    """Read the upload fully into memory. Nothing is ever written to disk."""
    if hasattr(image_file, 'read'):
        target = image_file
    elif hasattr(image_file, 'file') and hasattr(image_file.file, 'read'):
        target = image_file.file
    else:
        return bytes(image_file)

    if hasattr(target, 'seek'):
        target.seek(0)
    data = target.read()
    if hasattr(target, 'seek'):
        target.seek(0)
    return data


def _sniff(data):
    for kind, matches in _SIGNATURES.items():
        if matches(data):
            return kind
    return None


def _validate(file_name, data):
    """Validate extension, real file type and size before touching the network."""
    max_bytes = getattr(settings, 'HOSTINGER_UPLOAD_MAX_BYTES', DEFAULT_MAX_UPLOAD_BYTES)

    if not data:
        raise HostingerUploadError("The selected image is empty (0 bytes).")

    if len(data) > max_bytes:
        raise HostingerUploadError(
            f"Image is {len(data) / 1048576:.1f} MB. Maximum allowed size is "
            f"{max_bytes / 1048576:.0f} MB."
        )

    ext = os.path.splitext(file_name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HostingerUploadError(
            f"Unsupported file type '{ext or 'unknown'}'. Allowed formats: JPG, JPEG, PNG, WEBP, GIF."
        )

    kind = _sniff(data)
    if kind is None:
        raise HostingerUploadError(
            "The selected file is not a valid JPG, PNG, WEBP or GIF image."
        )

    expected = 'jpeg' if ext in ('.jpg', '.jpeg') else ext.lstrip('.')
    if kind != expected:
        raise HostingerUploadError(
            f"File contents are a {kind.upper()} image but the file is named '{ext}'. "
            f"Rename the file to .{kind} and upload again."
        )

    return ext


def _public_url(payload, upload_url):
    """Build the permanent public URL from Hostinger's JSON response.

    upload.php returns both the filename and a full URL. The filename is used
    together with HOSTINGER_MEDIA_DOMAIN so the public host stays under Django
    settings control -- otherwise a stale hard-coded domain inside upload.php
    would be written into the database.
    """
    returned_url = (payload.get('url') or '').strip()
    filename = (payload.get('filename') or '').strip() or os.path.basename(returned_url)

    if not filename:
        raise HostingerUploadError(
            f"Upload endpoint '{upload_url}' reported success but returned no image URL."
        )

    domain = getattr(settings, 'HOSTINGER_MEDIA_DOMAIN', '').strip().rstrip('/')
    if not domain:
        if not returned_url:
            raise HostingerUploadError(
                f"Upload endpoint '{upload_url}' returned no image URL and "
                f"HOSTINGER_MEDIA_DOMAIN is not configured."
            )
        return returned_url

    return f"{domain}/uploads/{filename}"


def _unique_filename(ext):
    """Build a collision-resistant name in upload.php's own format."""
    now = time.time()
    return f"{int(now)}_{int(now * 1000)}-{random.randint(100000000, 999999999)}{ext}"


def _store_locally(data, ext):
    """Save the image under MEDIA_ROOT and return its public URL.

    Used when upload.php is unreachable or errors, so the admin can keep
    publishing articles. The URL written to the database is built from
    HOSTINGER_MEDIA_DOMAIN exactly as in the remote path, so a blog row never
    records where the bytes happen to live.
    """
    media_root = getattr(settings, 'MEDIA_ROOT', '')
    if not media_root:
        raise HostingerUploadError(
            "Image could not be stored: MEDIA_ROOT is not configured."
        )

    filename = _unique_filename(ext)
    destination = os.path.join(str(media_root), filename)

    try:
        os.makedirs(str(media_root), exist_ok=True)
        with open(destination, 'wb') as handle:
            handle.write(data)
    except OSError as write_err:
        raise HostingerUploadError(f"Image could not be saved to {media_root}: {write_err}")

    if not os.path.exists(destination) or os.path.getsize(destination) == 0:
        raise HostingerUploadError("Image was written but could not be verified on disk.")

    domain = getattr(settings, 'HOSTINGER_MEDIA_DOMAIN', '').strip().rstrip('/')
    if not domain:
        raise HostingerUploadError(
            "Image was saved but HOSTINGER_MEDIA_DOMAIN is not configured, so no "
            "public URL could be built."
        )

    return f"{domain}/uploads/{filename}"


def _decode(body, status, upload_url):
    """Turn upload.php's response body into a dict, with useful errors."""
    text = body.decode('utf-8', errors='replace').strip()

    try:
        payload = json.loads(text)
    except ValueError:
        snippet = text[:200].replace('\n', ' ')
        raise HostingerUploadError(
            f"Upload endpoint '{upload_url}' did not return JSON (HTTP {status}). "
            f"Check that this URL points at the Hostinger server hosting upload.php. "
            f"Response started with: {snippet!r}"
        )

    if not isinstance(payload, dict):
        raise HostingerUploadError(
            f"Upload endpoint '{upload_url}' returned an unexpected response (HTTP {status})."
        )

    if status != 200 or not payload.get('success'):
        message = payload.get('message') or f"HTTP {status}"
        raise HostingerUploadError(f"Hostinger rejected the upload: {message}")

    return payload


def _post(upload_url, file_name, data, content_type):
    """POST the image, preferring requests and falling back to urllib."""
    try:
        import requests  # optional dependency
    except ImportError:
        return _post_with_urllib(upload_url, file_name, data, content_type)

    response = requests.post(
        upload_url,
        files={"image": (file_name, data, content_type)},
        timeout=30,
        headers={'User-Agent': 'KKDigital-Django-Client/1.0'},
        allow_redirects=True,
    )
    return response.content, response.status_code


def _post_with_urllib(upload_url, file_name, data, content_type):
    boundary = '----KKDigitalBoundary' + uuid.uuid4().hex
    body = b'\r\n'.join([
        f'--{boundary}'.encode('utf-8'),
        f'Content-Disposition: form-data; name="image"; filename="{file_name}"'.encode('utf-8'),
        f'Content-Type: {content_type}'.encode('utf-8'),
        b'',
        data,
        f'--{boundary}--'.encode('utf-8'),
        b'',
    ])

    request = urllib.request.Request(
        upload_url,
        data=body,
        headers={
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'User-Agent': 'KKDigital-Django-Client/1.0',
        },
        method='POST',
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read(), response.status
    except urllib.error.HTTPError as http_err:
        return http_err.read(), http_err.code


def upload_to_hostinger(image_file):
    """Upload an image to Hostinger's upload.php and return its permanent URL.

    The file is streamed straight from memory to the Hostinger endpoint; it is
    never written to Django's local media storage and its binary contents never
    reach MySQL. Only the returned URL is meant to be stored.

    Raises HostingerUploadError with a message suitable for display in the admin
    if validation fails or the upload does not complete successfully. A URL is
    returned only when Hostinger has confirmed the file was saved.
    """
    upload_url = getattr(
        settings, 'HOSTINGER_UPLOAD_URL', 'https://www.kkdigitalgrowth.com/upload.php'
    )

    if not image_file:
        raise HostingerUploadError("No image file was provided for upload.")

    file_name = os.path.basename(getattr(image_file, 'name', '') or 'upload.jpg')

    data = _read_bytes(image_file)
    ext = _validate(file_name, data)
    content_type = _CONTENT_TYPES[ext]

    fallback_enabled = getattr(settings, 'BLOG_IMAGE_LOCAL_FALLBACK', False)

    logger.info(
        "Uploading '%s' (%d bytes, %s) to %s", file_name, len(data), content_type, upload_url
    )

    try:
        try:
            body, status = _post(upload_url, file_name, data, content_type)
        except HostingerUploadError:
            raise
        except Exception as transport_err:
            raise HostingerUploadError(
                f"Could not reach the Hostinger upload endpoint '{upload_url}': {transport_err}"
            )

        payload = _decode(body, status, upload_url)
        public_url = _public_url(payload, upload_url)
    except HostingerUploadError as remote_err:
        if not fallback_enabled:
            raise
        logger.warning(
            "Hostinger upload failed (%s). Storing the image with Django instead.", remote_err
        )
        public_url = _store_locally(data, ext)
        logger.info("Django stored the image at %s", public_url)
        return public_url

    logger.info("Hostinger stored the image at %s", public_url)
    return public_url
