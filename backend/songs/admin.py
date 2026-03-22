from django.contrib import admin
from .models import Song, GenreTag, MoodTag, OccasionTag

@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'status', 'creation_date')
    list_filter = ('status', 'genres')
    search_fields = ('title', 'prompt_text')

admin.site.register(GenreTag)
admin.site.register(MoodTag)
admin.site.register(OccasionTag)