"""
core/tasks.py
Async click logging.

Runs via Celery when a broker is available, but the app also calls
this function synchronously as a fallback (see redirect.py).
"""
try:
    from celery import shared_task
except ImportError:
    # Celery not installed — provide a passthrough decorator
    # so the function can still be called directly.
    def shared_task(func):
        func.delay = func
        return func

from django.utils import timezone
from django.db.models import Q


@shared_task
def log_click(short_code, ip_address, user_agent_string, referrer):
    """Log a single click event for analytics."""
    try:
        from core.models import ShortenedLink
        from analytics.models import ClickEvent

        link = ShortenedLink.objects.filter(
            Q(short_code=short_code) | Q(custom_alias=short_code)
        ).first()

        if not link:
            return

        # Parse user-agent safely.
        device = 'Other'
        browser = 'Unknown'
        try:
            from user_agents import parse
            ua = parse(user_agent_string)
            if ua.is_mobile:
                device = 'Mobile'
            elif ua.is_tablet:
                device = 'Tablet'
            elif ua.is_pc:
                device = 'PC'
            elif ua.is_bot:
                device = 'Bot'
            browser = ua.browser.family or 'Unknown'
        except Exception:
            pass  # user-agents lib missing or parse failed.

        ClickEvent.objects.create(
            link=link,
            ip_address=ip_address,
            user_agent=user_agent_string,
            device=device,
            browser=browser,
            referrer=referrer or '',
            timestamp=timezone.now(),
        )
    except Exception:
        # Never let analytics crash the redirect pipeline.
        pass

@shared_task
def send_welcome_email_task(user_email, username):
    from django.core.mail import send_mail
    from django.conf import settings
    subject = "Welcome to Trimrr!"
    message = f"Hello {username},\n\nWelcome to Trimrr — your new Liquid Smooth URL Shortener!\n\nWe provide the sharpest link management experience. Let us know if you need any help.\n\nBest,\nThe Trimrr Team"
    
    try:
        send_mail(
            subject,
            message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'Trimrr <noreply@trimrr.co>'),
            [user_email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Failed to send welcome email to {user_email}: {str(e)}")

