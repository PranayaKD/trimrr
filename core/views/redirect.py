"""
core/views/redirect.py
The redirect engine — the single most performance-critical view in the app.
"""
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views import View
from django.db import models

from core.models import ShortenedLink
from core.views.helpers import (
    safe_cache_get, safe_cache_set, get_client_ip,
)


class LinkRedirectView(View):
    """
    Resolves a short code / custom alias to its original URL
    and redirects the visitor.  Logs the click asynchronously.
    """

    def get(self, request, short_code):
        # ── 1. Cache Lookup (fast path) ─────────────────────────
        cached_url = safe_cache_get(f"link:{short_code}")

        if cached_url:
            self._log_click(request, short_code)
            return redirect(cached_url)

        # ── 2. DB Lookup (cache miss) ───────────────────────────
        link = (
            ShortenedLink.objects
            .filter(
                models.Q(short_code=short_code) | models.Q(custom_alias=short_code)
            )
            .filter(is_active=True)
            .only('original_url', 'custom_alias', 'expires_at')
            .first()
        )

        if not link:
            return render(request, '404.html', status=404)

        # ── 3. Expiry Check ─────────────────────────────────────
        if link.expires_at and link.expires_at < timezone.now():
            return render(
                request, '404.html',
                context={'error': 'Link has expired'},
                status=410,
            )

        # ── 4. Warm Cache ───────────────────────────────────────
        safe_cache_set(f"link:{short_code}", link.original_url, timeout=86400)
        if link.custom_alias:
            safe_cache_set(f"link:{link.custom_alias}", link.original_url, timeout=86400)

        # ── 5. Log Click ────────────────────────────────────────
        self._log_click(request, short_code)

        return redirect(link.original_url)

    # ── Private helpers ─────────────────────────────────────────

    @staticmethod
    def _log_click(request, short_code):
        """
        Try async Celery first.  If the broker is unreachable,
        fall back to synchronous logging so we never lose data.
        """
        from core.tasks import log_click

        ip = get_client_ip(request)
        ua = request.META.get('HTTP_USER_AGENT', '')
        ref = request.META.get('HTTP_REFERER', '')

        try:
            log_click.delay(short_code, ip, ua, ref)
        except Exception:
            # Broker down — run synchronously.
            try:
                log_click(short_code, ip, ua, ref)
            except Exception:
                pass  # Analytics loss is acceptable; never crash on redirect.
