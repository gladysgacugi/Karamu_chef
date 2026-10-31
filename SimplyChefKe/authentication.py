"""How the API knows who is logged in. Kept on its own: DRF imports it while it is still loading itself."""

from rest_framework import authentication
from rest_framework.permissions import SAFE_METHODS


class SessionAuthentication(authentication.SessionAuthentication):
    """The site's login session. DRF only checks the CSRF token of logged-in users; this checks it for everyone, so no
    other site can post our forms (including logging someone in to an account of the attacker's)."""

    def authenticate(self, request):
        user_auth = super().authenticate(request)
        if user_auth is None and request.method not in SAFE_METHODS:
            self.enforce_csrf(request)
        return user_auth
