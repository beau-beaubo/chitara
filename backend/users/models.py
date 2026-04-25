from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # Abstracted from GoogleOAuthUID to ExternalID
    external_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    
    # Standard profile fields
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    last_auth_date = models.DateTimeField(null=True, blank=True)

    # In models.py
    def save(self, *args, **kwargs):
        # Standard save is sufficient; AbstractUser already handles unusable passwords 
        # if no password is provided during create_user.
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.external_id or 'Local Admin'})"