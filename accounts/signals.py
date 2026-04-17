from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from payments.models import Subscription

# We can trigger an email on create via Celery.
from core.tasks import send_welcome_email_task

@receiver(post_save, sender=User)
def handle_new_user(sender, instance, created, **kwargs):
    if created:
        try:
            # Create a default 'free' subscription plan for the new user.
            # Use get_or_create to be idempotent and avoid 500s if called twice.
            Subscription.objects.get_or_create(user=instance, defaults={'plan': 'free'})
        except Exception as e:
            # Log the error but don't crash the signup flow.
            print(f"Error creating subscription for {instance.email}: {e}")
