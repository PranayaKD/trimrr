from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/links/', views.MyLinksView.as_view(), name='my_links'),
    path('dashboard/settings/', views.SettingsView.as_view(), name='settings'),
    path('dashboard/stats/', views.DashboardStatsView.as_view(), name='dashboard_stats'),
    path('analytics/<str:short_code>/', views.AnalyticsView.as_view(), name='link_analytics'),
    path('delete-link/<int:pk>/', views.ShortenedLinkDeleteView.as_view(), name='delete_link'),
    path('pricing/', views.PricingView.as_view(), name='pricing'),
    path('create-link/', views.HomeView.as_view(), name='create_link'),
    path('qr/', views.QRGeneratorView.as_view(), name='qr_generator'),
    path('qr-image/', views.qr_image_view, name='qr_image'),
    path('privacy/', views.PrivacyView.as_view(), name='privacy'),
    path('terms/', views.TermsView.as_view(), name='terms'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('<str:short_code>/', views.LinkRedirectView.as_view(), name='redirect'),
]
