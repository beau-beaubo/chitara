from django.db import models


class GenreTag(models.Model):
    name = models.CharField(max_length=50, unique=True)  # Pop, Rock, Classical

    def __str__(self) -> str:
        return self.name


class MoodTag(models.Model):
    name = models.CharField(max_length=50, unique=True)  # Happy, Sad, Energetic

    def __str__(self) -> str:
        return self.name


class OccasionTag(models.Model):
    name = models.CharField(max_length=50, unique=True)  # Birthday, Graduation, Workout

    def __str__(self) -> str:
        return self.name
