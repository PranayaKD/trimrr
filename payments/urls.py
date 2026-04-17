from django.urls import path
from . import views

urlpatterns = [
    path('checkout/', views.create_checkout_session, name='checkout_pro'),
    path('callback/', views.razorpay_callback, name='razorpay_callback'),
]
