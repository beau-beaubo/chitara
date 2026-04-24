from django.core.management.base import BaseCommand

from songs.models import GenreTag, MoodTag, OccasionTag


class Command(BaseCommand):
    help = "Seed default Genre/Mood/Occasion tags"

    def handle(self, *args, **options):
        genres = ["Pop", "Rock", "Classical", "Lo-fi", "Jazz", "Hip-Hop"]
        moods = ["Happy", "Sad", "Energetic", "Calm", "Romantic"]
        occasions = ["Birthday", "Workout", "Study", "Road Trip", "Wedding"]

        for name in genres:
            GenreTag.objects.get_or_create(name=name)

        for name in moods:
            MoodTag.objects.get_or_create(name=name)

        for name in occasions:
            OccasionTag.objects.get_or_create(name=name)

        self.stdout.write(self.style.SUCCESS("Seeded default tags"))
