from django.urls import path

from .views import (
    mock_audio_wav,
    shared_song_detail,
    songs_detail,
    songs_download,
    songs_generate,
    songs_list_create,
    songs_share,
    tags_list,
)

urlpatterns = [
    path("tags/", tags_list, name="tags_list"),
    path("songs/", songs_list_create, name="songs_list_create"),
    path("songs/<int:song_id>/", songs_detail, name="songs_detail"),
    path("songs/<int:song_id>/generate/", songs_generate, name="songs_generate"),
    path("songs/<int:song_id>/share/", songs_share, name="songs_share"),
    path("songs/<int:song_id>/download/", songs_download, name="songs_download"),
    path("shared/<str:share_hash>/", shared_song_detail, name="shared_song_detail"),
    path("mock-audio/<str:task_id>.wav", mock_audio_wav, name="mock_audio_wav"),
]
