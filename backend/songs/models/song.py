from django.conf import settings
from django.db import models


class SongStatus(models.TextChoices):
    PENDING = "Pending", "Pending"
    PROCESSING = "Processing", "Processing"
    COMPLETED = "Completed", "Completed"
    FAILED = "Failed", "Failed"


class Song(models.Model):
    title = models.CharField(max_length=255)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="songs",
    )
    creation_date = models.DateTimeField(auto_now_add=True)
    file_path = models.CharField(max_length=500, blank=True, null=True)
    file_type = models.CharField(max_length=20, blank=True, null=True)

    # External generation tracking (e.g., Suno taskId)
    generation_task_id = models.CharField(max_length=64, blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=SongStatus.choices,
        default=SongStatus.PENDING,
    )

    prompt_text = models.TextField()
    voice_type = models.CharField(max_length=100)
    duration = models.PositiveIntegerField(
        help_text="Duration in seconds",
        blank=True,
        null=True,
    )

    is_shared = models.BooleanField(default=False)
    share_hash = models.CharField(max_length=64, blank=True, null=True, unique=True)

    genres = models.ManyToManyField("GenreTag")
    moods = models.ManyToManyField("MoodTag")
    occasions = models.ManyToManyField("OccasionTag")

    def __str__(self) -> str:
        return self.title
