# users/oauth2.py
from social_core.backends.google import GoogleOAuth2

class GoogleOAuth2Custom(GoogleOAuth2):
    name = 'google-oauth2'

    def get_redirect_uri(self, state=None):
        # This will try to get the setting, but fallback to the dynamic URL
        # which is usually more reliable during development.
        return self.setting('REDIRECT_URI') or super().get_redirect_uri(state)