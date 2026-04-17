from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from payments.models import Subscription

# We can trigger an email on create via Celery.
from core.tasks import send_welcome_email_task

@receiver(post_save, sender=User)
def handle_new_user(sender, instance, created, **kwargs):
    if created:
        # Create a default 'free' subscription plan for the new user.
        Subscription.objects.create(user=instance, plan='free')
        
        # Dispatch the async celery task locally or asynchronously
        send_welcome_email_task.delay(instance.email, instance.username or instance.email)
