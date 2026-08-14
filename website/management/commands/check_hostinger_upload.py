"""Diagnose the Django -> Hostinger blog image upload path.

Usage:
    python manage.py check_hostinger_upload            # inspect config + endpoint
    python manage.py check_hostinger_upload --upload   # also send a real test image

Read-only by default. Touches no database table and no existing blog data.
"""
import io
import urllib.error
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand

# Smallest valid 1x1 transparent PNG, used only for the optional live test.
TEST_PNG = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
    b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\xf8\x0f'
    b'\x00\x01\x01\x01\x00\x18\xdd\x8a\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
)


class Command(BaseCommand):
    help = "Check that the Hostinger upload endpoint and public image URLs are reachable."

    def add_arguments(self, parser):
        parser.add_argument(
            '--upload',
            action='store_true',
            help="Send a real 1x1 test PNG to the endpoint and verify the returned URL loads.",
        )

    def _fetch(self, url, method='GET'):
        request = urllib.request.Request(
            url, method=method, headers={'User-Agent': 'KKDigital-Django-Client/1.0'}
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, dict(response.headers), response.read(400)
        except urllib.error.HTTPError as http_err:
            return http_err.code, dict(http_err.headers), http_err.read(400)
        except Exception as err:
            return None, {}, str(err).encode()

    def _diagnose(self, status, headers, body):
        """Explain who answered, which is the whole point of this command."""
        server = headers.get('Server', 'unknown')
        text = body.decode('utf-8', errors='replace')

        if 'Page not found at' in text or 'DJANGO_SETTINGS_MODULE' in text:
            self.stdout.write(self.style.ERROR(
                f"    -> Answered by DJANGO (Server: {server}), not Hostinger PHP.\n"
                f"       This hostname routes to your Django app, so upload.php never runs.\n"
                f"       Point this hostname at the Hostinger server that owns public_html."
            ))
            return False

        if server.lower().startswith('vercel'):
            self.stdout.write(self.style.ERROR(
                f"    -> Answered by VERCEL, not Hostinger. upload.php cannot execute there."
            ))
            return False

        if status is None:
            self.stdout.write(self.style.ERROR(f"    -> Host unreachable: {text}"))
            return False

        if 'litespeed' in server.lower() or 'apache' in server.lower():
            self.stdout.write(self.style.SUCCESS(
                f"    -> Answered by Hostinger ({server}). PHP is reachable on this host."
            ))
            return status < 500

        self.stdout.write(f"    -> Server: {server}")
        return status < 500

    def handle(self, *args, **options):
        upload_url = getattr(settings, 'HOSTINGER_UPLOAD_URL', '')
        media_domain = getattr(settings, 'HOSTINGER_MEDIA_DOMAIN', '')
        max_bytes = getattr(settings, 'HOSTINGER_UPLOAD_MAX_BYTES', 0)

        self.stdout.write(self.style.MIGRATE_HEADING("\n[1] Current configuration"))
        self.stdout.write(f"    HOSTINGER_UPLOAD_URL       = {upload_url}")
        self.stdout.write(f"    HOSTINGER_MEDIA_DOMAIN     = {media_domain}")
        self.stdout.write(f"    HOSTINGER_UPLOAD_MAX_BYTES = {max_bytes} ({max_bytes / 1048576:.0f} MB)")

        if not upload_url or not media_domain:
            self.stdout.write(self.style.ERROR(
                "\n    Both settings must be configured. Set them in .env and re-run."
            ))
            return

        self.stdout.write(self.style.MIGRATE_HEADING("\n[2] Test 1 - is upload.php served by Hostinger?"))
        self.stdout.write(f"    GET {upload_url}")
        status, headers, body = self._fetch(upload_url)
        self.stdout.write(f"    HTTP {status}")
        endpoint_ok = self._diagnose(status, headers, body)

        self.stdout.write(self.style.MIGRATE_HEADING("\n[3] Test 3 - is /uploads/ served by Hostinger?"))
        probe = f"{media_domain.rstrip('/')}/uploads/"
        self.stdout.write(f"    GET {probe}")
        status, headers, body = self._fetch(probe)
        self.stdout.write(f"    HTTP {status}")
        self._diagnose(status, headers, body)

        if not options['upload']:
            self.stdout.write(self.style.WARNING(
                "\n    Re-run with --upload to send a real test image once the checks above pass.\n"
            ))
            return

        if not endpoint_ok:
            self.stdout.write(self.style.ERROR(
                "\n    Skipping the live upload: the endpoint is not served by Hostinger yet.\n"
            ))
            return

        self.stdout.write(self.style.MIGRATE_HEADING("\n[4] Test 2 - live upload"))
        from utils.upload_image import upload_to_hostinger, HostingerUploadError

        test_file = io.BytesIO(TEST_PNG)
        test_file.name = "django-connection-test.png"

        try:
            public_url = upload_to_hostinger(test_file)
        except HostingerUploadError as err:
            self.stdout.write(self.style.ERROR(f"    Upload rejected: {err}"))
            self.stdout.write(self.style.WARNING(
                "    Nothing would be saved to blogs.image - this is the intended safe behaviour.\n"
            ))
            return

        self.stdout.write(self.style.SUCCESS(f"    Uploaded. Django would store: {public_url}"))

        self.stdout.write("\n    Verifying the stored URL actually loads ...")
        status, headers, _ = self._fetch(public_url)
        content_type = headers.get('Content-Type', '')

        if status == 200 and content_type.startswith('image/'):
            self.stdout.write(self.style.SUCCESS(
                f"    HTTP 200, Content-Type: {content_type} - the full flow works end to end.\n"
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f"    HTTP {status}, Content-Type: {content_type or 'n/a'}.\n"
                f"    The file uploaded but its public URL does not serve an image.\n"
                f"    HOSTINGER_MEDIA_DOMAIN must point at the same Hostinger server.\n"
            ))
