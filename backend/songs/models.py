"""Model aggregation for the `songs` app.

Django auto-loads models from `songs.models`, but keeping everything in one file
gets hard to maintain as the domain grows. The actual model classes live in
separate modules and are re-exported here.
"""

from .song_models import Song, SongStatus
from .tag_models import GenreTag, MoodTag, OccasionTag

__all__ = [
    "Song",
    "SongStatus",
    "GenreTag",
    "MoodTag",
    "OccasionTag",
]