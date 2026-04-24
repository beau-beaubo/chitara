from __future__ import annotations

from datetime import datetime, timedelta

from django.contrib.auth import get_user_model, logout
from django.utils import timezone

from users.jwt_utils import JwtAuthError, parse_jwt_subject


class JwtAuthenticationMiddleware:
    """Authenticates requests using a Bearer JWT when no session user is present."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            token = self._extract_bearer_token(request)
            if token:
                self._attach_user_from_token(request, token)

        return self.get_response(request)

    @staticmethod
    def _extract_bearer_token(request) -> str | None:
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header:
            return None

        scheme, _, value = auth_header.partition(" ")
        if scheme.lower() != "bearer":
            return None

        token = value.strip()
        return token or None

    @staticmethod
    def _attach_user_from_token(request, token: str) -> None:
        try:
            user_id = parse_jwt_subject(token)
        except JwtAuthError:
            return

        User = get_user_model()
        user = User.objects.filter(pk=user_id).first()
        if user is None or not user.is_active:
            return

        request.user = user


class SevenDaySessionExpiryMiddleware:
    """Expires authenticated sessions 7 days after the last authentication event.

    Implementation notes:
    - `users.signals.set_last_auth_at` stores `last_auth_at` on login.
    - This middleware enforces the cutoff for any authenticated request.

    If `last_auth_at` is missing (e.g., legacy sessions), it is set to now.
    """

    _SESSION_KEY = "last_auth_at"
    _MAX_AGE = timedelta(days=7)

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            last_auth_raw = request.session.get(self._SESSION_KEY)

            last_auth_at = self._parse_iso_datetime(last_auth_raw)
            if last_auth_at is None:
                request.session[self._SESSION_KEY] = timezone.now().isoformat()
            else:
                now = timezone.now()
                if now - last_auth_at > self._MAX_AGE:
                    logout(request)
                    request.session.flush()

        return self.get_response(request)

    @staticmethod
    def _parse_iso_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value)
        except (TypeError, ValueError):
            return None

        if timezone.is_naive(parsed):
            return timezone.make_aware(parsed, timezone.get_current_timezone())
        return parsed
