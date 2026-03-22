from django.db import models
from django.conf import settings


# Enums based on SRS System Features
class SongStatus(models.TextChoices):
    PENDING = 'Pending', 'Pending'
    PROCESSING = 'Processing', 'Processing'
    COMPLETED = 'Completed', 'Completed'
    FAILED = 'Failed', 'Failed'

class Song(models.Model):
    # Core attributes
    title = models.CharField(max_length=255)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='songs'
    )
    creation_date = models.DateTimeField(auto_now_add=True)
    file_path = models.CharField(max_length=500, blank=True, null=True)
    
    # State management
    status = models.CharField(
        max_length=20, 
        choices=SongStatus.choices, 
        default=SongStatus.PENDING
    )
    
    # AI Generation Metadata
    prompt_text = models.TextField() 
    voice_type = models.CharField(max_length=100) 
    duration = models.PositiveIntegerField(help_text="Duration in seconds", blank=True, null=True)
    
    # Sharing attributes
    is_shared = models.BooleanField(default=False)
    share_hash = models.CharField(max_length=64, blank=True, null=True, unique=True)

    # Multiplicity 1..* implemented via Many-to-Many
    genres = models.ManyToManyField('GenreTag')
    moods = models.ManyToManyField('MoodTag')
    occasions = models.ManyToManyField('OccasionTag')

    def __str__(self):
        return self.title

# Tag models to allow multiple selections (e.g., Pop + Rock)
class GenreTag(models.Model):
    name = models.CharField(max_length=50, unique=True) # Pop, Rock, Classical
    def __str__(self): return self.name

class MoodTag(models.Model):
    name = models.CharField(max_length=50, unique=True) # Happy, Sad, Energetic
    def __str__(self): return self.name

class OccasionTag(models.Model):
    name = models.CharField(max_length=50, unique=True) # Birthday, Graduation, Workout
    def __str__(self): return self.name