"""
core/views/__init__.py
Re-exports all views so existing imports like
`from core.views import HomeView` continue to work.
"""

# ── Page Views (Template Rendering) ─────────────────────────────────
from core.views.pages import (
    custom_404_view,
    HomeView,
    DashboardView,
    DashboardStatsView,
    ShortenedLinkDeleteView,
    MyLinksView,
    AnalyticsView,
    PricingView,
    PrivacyView,
    TermsView,
    SettingsView,
    ContactView,
)

# ── Redirect Engine ─────────────────────────────────────────────────
from core.views.redirect import LinkRedirectView

# ── QR Code ─────────────────────────────────────────────────────────
from core.views.qr import QRGeneratorView, qr_image_view

# ── REST API ────────────────────────────────────────────────────────
from core.views.api import (
    LinkListCreateAPIView,
    LinkDetailAPIView,
    LinkStatsAPIView,
)

__all__ = [
    # Pages
    'custom_404_view',
    'HomeView',
    'DashboardView',
    'DashboardStatsView',
    'ShortenedLinkDeleteView',
    'MyLinksView',
    'AnalyticsView',
    'PricingView',
    'PrivacyView',
    'TermsView',
    'SettingsView',
    'ContactView',
    # Redirect
    'LinkRedirectView',
    # QR
    'QRGeneratorView',
    'qr_image_view',
    # API
    'LinkListCreateAPIView',
    'LinkDetailAPIView',
    'LinkStatsAPIView',
]
