from django.core.management.base import BaseCommand

from songs.models import GenreTag, MoodTag, OccasionTag


class Command(BaseCommand):
    help = "Seed default Genre/Mood/Occasion tags"

    def handle(self, *args, **options):
        # Domain model: Pop, Rock, Classical, R&B, Lo-fi, Jazz, Electronic
        genres = ["Pop", "Rock", "Classical", "R&B", "Lo-fi", "Jazz", "Electronic"]
        # Domain model: Happy, Sad, Energetic, Calm, Aggressive, Focus
        moods = ["Happy", "Sad", "Energetic", "Calm", "Aggressive", "Focus"]
        # Domain model: Birthday, Graduation, Workout, Study, Party
        occasions = ["Birthday", "Graduation", "Workout", "Study", "Party"]

        for name in genres:
            GenreTag.objects.get_or_create(name=name)

        for name in moods:
            MoodTag.objects.get_or_create(name=name)

        for name in occasions:
            OccasionTag.objects.get_or_create(name=name)

        self.stdout.write(self.style.SUCCESS("Seeded default tags"))
