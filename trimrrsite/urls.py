from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from accounts.views import (
    RegisterView, ProfileView, 
    ForgotPasswordView, ResetPasswordView
)
from core.views import (
    LinkListCreateAPIView, LinkDetailAPIView, LinkStatsAPIView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    
    # --- Auth API ---
    path('api/auth/register/', RegisterView.as_view(), name='api_register'),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/profile/', ProfileView.as_view(), name='api_profile'),
    path('api/auth/forgot-password/', ForgotPasswordView.as_view(), name='api_forgot_password'),
    path('api/auth/reset-password/', ResetPasswordView.as_view(), name='api_reset_password'),
    
    # --- Links API ---
    path('api/links/', LinkListCreateAPIView.as_view(), name='api_link_list'),
    path('api/links/<str:short_code>/', LinkDetailAPIView.as_view(), name='api_link_detail'),
    path('api/links/<str:short_code>/stats/', LinkStatsAPIView.as_view(), name='api_link_stats'),
    
    # --- Payments API ---
    path('payments/', include('payments.urls')),
    
    # --- Core Routes (Templates & Redirects) ---
    path('', include('core.urls')),
]

handler404 = 'core.views.custom_404_view'
