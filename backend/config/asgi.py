"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from pathlib import Path

from django.core.asgi import get_asgi_application


def _load_dotenv_if_present() -> None:
	env_path = Path(__file__).resolve().parent.parent.parent / ".env"
	if not env_path.exists():
		return
	try:
		from dotenv import load_dotenv
	except Exception:
		return
	load_dotenv(dotenv_path=env_path, override=True)


_load_dotenv_if_present()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_asgi_application()
