"""
core/views/helpers.py
Shared utility functions used across views.
"""
import hashlib
import re
from urllib.parse import urlparse

from django.core.cache import cache


# ── Safe Cache Wrappers ─────────────────────────────────────────────
# These silently absorb Redis failures so the app never 500s on cache.


def safe_cache_get(key, default=None):
    """Get a value from cache, returning default if Redis is down."""
    try:
        return cache.get(key, default)
    except Exception:
        return default


def safe_cache_set(key, value, timeout=86400):
    """Set a value in cache, silently failing if Redis is down."""
    try:
        cache.set(key, value, timeout=timeout)
    except Exception:
        pass


def safe_cache_delete(key):
    """Delete a key from cache, silently failing if Redis is down."""
    try:
        cache.delete(key)
    except Exception:
        pass


# ── IP Address Handling ─────────────────────────────────────────────


def get_client_ip(request):
    """
    Extract the real client IP from the request.

    Security: REMOTE_ADDR is the only trustworthy source because it
    comes from the TCP connection itself. X-Forwarded-For can be
    trivially spoofed by any client. We only fall back to it when
    REMOTE_ADDR is a known proxy loopback (meaning a reverse-proxy
    like Nginx or a load-balancer set it).
    """
    remote_addr = request.META.get('REMOTE_ADDR', '')

    # Only trust X-Forwarded-For if the direct connection is from
    # a local / private proxy (loopback or Docker bridge).
    trusted_proxies = ('127.0.0.1', '::1', '10.', '172.', '192.168.')
    if any(remote_addr.startswith(prefix) for prefix in trusted_proxies):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if x_forwarded_for:
            # First entry is the original client IP.
            return x_forwarded_for.split(',')[0].strip()

    return remote_addr


# ── URL Validation ──────────────────────────────────────────────────

# Known dangerous TLDs / patterns used in phishing campaigns.
BLOCKED_KEYWORDS = [
    'phishing', 'malware', 'hack', 'exploit',
]

BLOCKED_EXTENSIONS = [
    '.exe', '.bat', '.cmd', '.scr', '.msi', '.ps1',
]


def validate_url_safety(url):
    """
    Returns (is_safe: bool, error_message: str | None).
    """
    lower = url.lower()

    # Block dangerous keywords in URL body.
    for kw in BLOCKED_KEYWORDS:
        if kw in lower:
            return False, f"This URL contains a blocked keyword ('{kw}') and cannot be shortened."

    # Block direct-file download links.
    parsed = urlparse(lower)
    path = parsed.path
    for ext in BLOCKED_EXTENSIONS:
        if path.endswith(ext):
            return False, f"Direct links to executable files ({ext}) are not allowed."

    return True, None


def is_self_referencing_url(url, request):
    """
    Check if the user is trying to shorten a URL that points
    back to our own domain (redirect loop prevention).
    """
    parsed = urlparse(url)
    hostname = parsed.hostname or ''
    our_host = request.get_host().split(':')[0]

    blocked_hosts = {our_host, 'localhost', '127.0.0.1'}
    return hostname in blocked_hosts


# ── Alias Sanitization ──────────────────────────────────────────────

# Aliases must be alphanumeric + hyphens, 3-50 chars.
ALIAS_PATTERN = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9\-]{1,48}[a-zA-Z0-9]$')

# Reserved slugs that conflict with real routes.
RESERVED_SLUGS = frozenset({
    'admin', 'api', 'dashboard', 'analytics', 'pricing',
    'settings', 'qr', 'qr-image', 'contact', 'privacy',
    'terms', 'accounts', 'login', 'signup', 'logout',
    'static', 'media', 'favicon.ico', 'robots.txt',
    'delete-link', 'create-link',
})


def validate_alias(alias):
    """
    Returns (is_valid: bool, error_message: str | None).
    """
    if not alias:
        return True, None  # Alias is optional.

    if alias.lower() in RESERVED_SLUGS:
        return False, f"'{alias}' is a reserved word and cannot be used as an alias."

    if not ALIAS_PATTERN.match(alias):
        return False, "Alias must be 3-50 characters, alphanumeric and hyphens only."

    return True, None
