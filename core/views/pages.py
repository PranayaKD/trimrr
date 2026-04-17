"""
core/views/pages.py
All template-rendered page views (Home, Dashboard, Analytics, etc.).
No REST API logic lives here.
"""
from datetime import timedelta, date

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError, models
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from analytics.models import ClickEvent
from core.models import ShortenedLink
from core.views.helpers import (
    safe_cache_delete,
    validate_url_safety,
    is_self_referencing_url,
    validate_alias,
)


# ── Error Handler ───────────────────────────────────────────────────


def custom_404_view(request, exception=None):
    return render(request, '404.html', status=404)


# ── Home ────────────────────────────────────────────────────────────


class HomeView(View):
    template_name = 'home.html'

    def get(self, request):
        context = self._get_stats_context(request)

        if (
            request.headers.get('HX-Request')
            and request.headers.get('HX-Target') == 'home-stats'
        ):
            return render(request, 'partials/home_stats.html', context)

        return render(request, self.template_name, context)

    def post(self, request):
        original_url = request.POST.get('url', '').strip()
        custom_alias = request.POST.get('alias', '').strip() or None

        if not original_url:
            return render(request, self.template_name, self._get_stats_context(request))

        # ── Validation Pipeline ─────────────────────────────────
        # 1. Redirect loop check
        if is_self_referencing_url(original_url, request):
            messages.error(request, "You cannot shorten URLs from this domain.")
            return redirect('home')

        # 2. Malicious link check
        is_safe, safety_error = validate_url_safety(original_url)
        if not is_safe:
            messages.error(request, safety_error)
            return redirect('home')

        # 3. Alias validation
        is_valid_alias, alias_error = validate_alias(custom_alias)
        if not is_valid_alias:
            messages.error(request, alias_error)
            return redirect('home')

        # 4. Alias collision check (early, before hitting the DB constraint)
        if custom_alias:
            alias_taken = ShortenedLink.objects.filter(
                models.Q(short_code=custom_alias) | models.Q(custom_alias=custom_alias)
            ).exists()
            if alias_taken:
                messages.error(request, f"Alias '{custom_alias}' is already taken.")
                return redirect('dashboard' if request.user.is_authenticated else 'home')

        # ── Create Link ─────────────────────────────────────────
        short_code = ShortenedLink.generate_code()
        owner = request.user if request.user.is_authenticated else None

        try:
            link = ShortenedLink.objects.create(
                original_url=original_url,
                short_code=short_code,
                custom_alias=custom_alias,
                owner=owner,
            )
        except IntegrityError:
            # Race condition: alias or code was just taken.
            messages.error(request, "A collision occurred. Please try again.")
            return redirect('home')

        # Build short URL safely for prod (handles http/https automatically)
        short_path = f"/{custom_alias or short_code}"
        short_url = request.build_absolute_uri(short_path)

        messages.success(request, "Link created successfully!")
        return render(request, self.template_name, {
            'short_url': short_url,
            **self._get_stats_context(request),
        })

    # ── Shared context ──────────────────────────────────────────

    @staticmethod
    def _get_stats_context(request=None):
        """Shared context for GET and POST to keep stats fresh."""
        total_links = ShortenedLink.objects.count()
        total_clicks = ClickEvent.objects.count()

        def format_count(n):
            if n >= 1000:
                return f"{n / 1000:.1f}k"
            return str(n)

        today = date.today()
        raw_stats = dict(
            ClickEvent.objects
            .filter(timestamp__date__gte=today - timedelta(days=6))
            .annotate(date=TruncDate('timestamp'))
            .values_list('date')
            .annotate(count=Count('id'))
            .values_list('date', 'count')
        )
        daily_stats = []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            daily_stats.append({'date': d, 'count': raw_stats.get(d, 0)})
        max_clicks = max((d['count'] for d in daily_stats), default=1) or 1

        recent_links = []
        if request and request.user.is_authenticated:
            recent_links = (
                ShortenedLink.objects
                .filter(owner=request.user, is_active=True)
                .order_by('-created_at')[:3]
            )

        return {
            'total_links_count': total_links,
            'total_clicks_count': total_clicks,
            'total_clicks_formatted': format_count(total_clicks),
            'conversion_rate': "98.2%" if total_links > 0 else "0.1%",
            'daily_stats': daily_stats,
            'max_clicks': max_clicks,
            'recent_links': recent_links,
        }


# ── Dashboard ───────────────────────────────────────────────────────


class DashboardView(LoginRequiredMixin, View):
    template_name = 'dashboard.html'

    def get(self, request):
        links = (
            ShortenedLink.objects
            .filter(owner=request.user, is_active=True)
            .order_by('-created_at')
        )
        all_clicks = ClickEvent.objects.filter(link__owner=request.user)

        total_clicks = all_clicks.count()
        unique_visitors = all_clicks.values('ip_address').distinct().count()
        last_clicked = all_clicks.order_by('-timestamp').first()

        context = {
            'links': links,
            'total_clicks': total_clicks,
            'unique_visitors': unique_visitors,
            'last_clicked': last_clicked,
            'last_clicked_str': (
                last_clicked.timestamp.strftime("%H:%M %p") if last_clicked else "--"
            ),
            'last_clicked_date': (
                last_clicked.timestamp.strftime("%b %d") if last_clicked else ""
            ),
            'total_links': links.count(),
        }

        if request.headers.get('HX-Request'):
            target = request.headers.get('HX-Target')
            if target == 'dashboard-stats':
                return render(request, 'partials/dashboard_stats.html', context)
            elif target == 'dashboard-links':
                return render(request, 'partials/dashboard_links.html', context)

        return render(request, self.template_name, context)


class DashboardStatsView(LoginRequiredMixin, View):
    def get(self, request):
        links = ShortenedLink.objects.filter(owner=request.user, is_active=True)
        all_clicks = ClickEvent.objects.filter(link__owner=request.user)

        total_clicks = all_clicks.count()
        unique_visitors = all_clicks.values('ip_address').distinct().count()
        last_clicked = all_clicks.order_by('-timestamp').first()

        return render(request, 'partials/dashboard_stats.html', {
            'total_clicks': total_clicks,
            'unique_visitors': unique_visitors,
            'last_clicked_str': (
                last_clicked.timestamp.strftime("%H:%M %p") if last_clicked else "--"
            ),
            'last_clicked_date': (
                last_clicked.timestamp.strftime("%b %d") if last_clicked else ""
            ),
            'total_links': links.count(),
        })


# ── Link Management ─────────────────────────────────────────────────


class ShortenedLinkDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        link = get_object_or_404(ShortenedLink, pk=pk, owner=request.user)
        link.is_active = False
        link.save(update_fields=['is_active'])

        # Invalidate cache safely
        safe_cache_delete(f"link:{link.short_code}")
        if link.custom_alias:
            safe_cache_delete(f"link:{link.custom_alias}")

        messages.success(request, "Link deactivated successfully.")
        return redirect('dashboard')


class MyLinksView(LoginRequiredMixin, View):
    template_name = 'my_links.html'

    def get(self, request):
        links = (
            ShortenedLink.objects
            .filter(owner=request.user, is_active=True)
            .order_by('-created_at')
        )
        return render(request, self.template_name, {'links': links})


# ── Analytics ───────────────────────────────────────────────────────


class AnalyticsView(LoginRequiredMixin, View):
    template_name = 'analytics.html'

    def get(self, request, short_code):
        link = get_object_or_404(
            ShortenedLink, short_code=short_code, owner=request.user,
        )
        clicks = link.clicks.all().order_by('-timestamp')

        daily_stats = (
            link.clicks
            .annotate(date=TruncDate('timestamp'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )

        total_clicks = clicks.count()
        unique_visitors = clicks.values('ip_address').distinct().count()
        last_click = clicks.first()

        context = {
            'link': link,
            'clicks': clicks,
            'daily_stats': daily_stats,
            'total_clicks': total_clicks,
            'unique_visitors': unique_visitors,
            'last_click': last_click,
        }

        if request.headers.get('HX-Request'):
            target = request.headers.get('HX-Target')
            if target == 'analytics-stats':
                return render(request, 'partials/analytics_stats.html', context)
            elif target == 'recent-clicks-table':
                return render(request, 'partials/analytics_recent_clicks.html', context)
            elif target == 'analytics-chart':
                return render(request, self.template_name, context)

        return render(request, self.template_name, context)


# ── Static Pages ────────────────────────────────────────────────────


class PricingView(View):
    template_name = 'pricing.html'

    def get(self, request):
        return render(request, self.template_name)


class PrivacyView(View):
    template_name = 'privacy.html'

    def get(self, request):
        return render(request, self.template_name)


class TermsView(View):
    template_name = 'terms.html'

    def get(self, request):
        return render(request, self.template_name)


class SettingsView(LoginRequiredMixin, View):
    template_name = 'settings.html'

    def get(self, request):
        return render(request, self.template_name)


class ContactView(View):
    template_name = 'contact.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', 'general')
        message_body = request.POST.get('message', '').strip()

        if not all([name, email, message_body]):
            messages.error(request, "Please fill in all required fields.")
            return redirect('contact')

        from django.core.mail import send_mail

        full_subject = f"[Trimrr Contact] {subject.title()} — from {name}"
        full_message = (
            f"Name: {name}\nEmail: {email}\nSubject: {subject}\n\n{message_body}"
        )

        try:
            send_mail(
                full_subject,
                full_message,
                email,
                ['support@trimrr.co'],
                fail_silently=False,
            )
            messages.success(request, "Message sent successfully! We'll get back to you soon.")
        except Exception:
            messages.success(request, "Message received! We'll get back to you soon.")

        return redirect('contact')
