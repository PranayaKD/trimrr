from django.db import models
from django.conf import settings
from django.utils import timezone
import string
import secrets


class ShortenedLink(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='links',
        null=True,
        blank=True,
    )
    original_url = models.URLField(max_length=10000)
    short_code = models.CharField(max_length=20, unique=True, db_index=True)
    custom_alias = models.CharField(
        max_length=50, unique=True, null=True, blank=True, db_index=True,
    )
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            # Speed up the redirect lookup — the hottest query in the app.
            models.Index(fields=['short_code', 'is_active']),
        ]

    def __str__(self):
        return f"{self.short_code} -> {self.original_url[:50]}"

    @staticmethod
    def generate_code(length=6):
        """Generate a unique random short code."""
        chars = string.ascii_letters + string.digits
        for _ in range(10):  # Bounded retries instead of infinite while-loop.
            code = ''.join(secrets.choice(chars) for _ in range(length))
            if not ShortenedLink.objects.filter(short_code=code).exists():
                return code
        # Extremely unlikely fallback: increase length.
        return ShortenedLink.generate_code(length=length + 1)
