from pathlib import Path

from django.contrib import admin
from django.http import FileResponse
from django.urls import include, path
from django.views.static import serve

from social_django.views import auth as social_auth, complete as social_complete
from users.views import google_jwt_redirect

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR.parent / 'frontend'


def frontend_index(_request, **_kwargs):
    return FileResponse(open(FRONTEND_DIR / 'index.html', 'rb'), content_type='text/html')


def frontend_css(request, path):
    return serve(request, path, document_root=FRONTEND_DIR / 'css')


def frontend_js(request, path):
    return serve(request, path, document_root=FRONTEND_DIR / 'js')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('social_django.urls', namespace='social')),
    path('api/auth/google/login/', social_auth, {'backend': 'google-oauth2'}, name='google_login'),
    path('api/auth/google/callback/', social_complete, {"backend": "google-oauth2"}, name='google_callback'),
    path('api/auth/google/jwt-redirect/', google_jwt_redirect, name='google_jwt_redirect'),
    path('api/', include('songs.urls')),
    path('api/user/', include('users.urls')),
    # Serve frontend static assets
    path('css/<path:path>', frontend_css),
    path('js/<path:path>', frontend_js),
    # SPA routes — serve index.html for root and /shared/<hash>/
    path('shared/<str:share_hash>/', frontend_index),
    path('', frontend_index),
]
