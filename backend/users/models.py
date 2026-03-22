from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # Abstracted from GoogleOAuthUID to ExternalID
    external_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    
    # Standard profile fields
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)

    def save(self, *args, **kwargs):
        # Logic: Authentication is external, so we don't use local passwords
        if not self.password:
            self.set_unusable_password()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.external_id or 'Local Admin'})"