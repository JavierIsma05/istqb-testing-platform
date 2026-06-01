from django.db import models
from django.conf import settings


class Profile(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    full_name = models.CharField(max_length=255)

    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True
    )

    bio = models.TextField(blank=True)

    def __str__(self):
        return self.full_name