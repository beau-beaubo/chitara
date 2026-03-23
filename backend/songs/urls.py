from django.urls import path

from . import api_views

urlpatterns = [
    path("songs/", api_views.songs_list_create, name="songs_list_create"),
    path("songs/<int:song_id>/", api_views.songs_detail, name="songs_detail"),
]
