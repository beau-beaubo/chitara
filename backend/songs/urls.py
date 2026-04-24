from django.urls import path

from . import api_views

urlpatterns = [
    path("tags/", api_views.tags_list, name="tags_list"),
    path("songs/", api_views.songs_list_create, name="songs_list_create"),
    path("songs/<int:song_id>/", api_views.songs_detail, name="songs_detail"),
    path(
        "songs/<int:song_id>/generate/",
        api_views.songs_generate,
        name="songs_generate",
    ),
    path("songs/<int:song_id>/share/", api_views.songs_share, name="songs_share"),
    path(
        "songs/<int:song_id>/download/",
        api_views.songs_download,
        name="songs_download",
    ),
    path("shared/<str:share_hash>/", api_views.shared_song_detail, name="shared_song_detail"),
    path(
        "mock-audio/<str:task_id>.wav",
        api_views.mock_audio_wav,
        name="mock_audio_wav",
    ),
]
