from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class Subscription(models.Model):
    PLAN_CHOICES = [
        ('free', 'Free'),
        ('pro', 'Pro'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free')
    razorpay_customer_id = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    current_period_start = models.DateTimeField(default=timezone.now)
    current_period_end = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.plan}"
        
    def activate_pro(self):
        self.plan = 'pro'
        self.current_period_start = timezone.now()
        self.current_period_end = timezone.now() + timedelta(days=365)
        self.is_active = True
        self.save()

class PaymentTransaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    razorpay_order_id = models.CharField(max_length=255, unique=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=512, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2) # In INR usually
    status = models.CharField(max_length=50, default='created') # created, paid, failed
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Order: {self.razorpay_order_id} - User: {self.user.email} - Status: {self.status}"
