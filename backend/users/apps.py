from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self) -> None:
        # Register auth-related signals (e.g., last-auth timestamp).
        from . import signals  # noqa: F401
