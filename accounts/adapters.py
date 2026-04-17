from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse

class TrimrrAccountAdapter(DefaultAccountAdapter):
    def get_signup_redirect_url(self, request):
        """After signup, send them to the login page."""
        return reverse('account_login')

    def get_login_redirect_url(self, request):
        """After login, send them to the home page."""
        return reverse('home')
