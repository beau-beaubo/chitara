from __future__ import annotations

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils import timezone


@receiver(user_logged_in)
def set_last_auth_at(sender, request, user, **kwargs):  # type: ignore[no-untyped-def]
    """Track last authentication time for session-expiry enforcement.

    This supports the SRS requirement of automatically terminating sessions
    7 days after the last authentication event.
    """

    if request is None:
        return

    request.session["last_auth_at"] = timezone.now().isoformat()
