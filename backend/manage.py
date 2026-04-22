#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path


def _load_dotenv_if_present() -> None:
    """Load environment variables from repo-root .env (if present).

    This keeps local secrets (e.g., SUNO_API_KEY) out of git while allowing
    configuration via a simple `.env` file.
    """

    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return

    try:
        from dotenv import load_dotenv
    except Exception:
        return

    load_dotenv(dotenv_path=env_path, override=True)


def main():
    """Run administrative tasks."""
    _load_dotenv_if_present()
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
