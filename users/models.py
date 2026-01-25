from django.conf import settings
from django.db import models

class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    hospital_default = models.CharField(max_length=200, blank=True, default="")

    def __str__(self):
        return f"Profile({self.user.username})"
