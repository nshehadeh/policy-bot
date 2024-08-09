from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    chat_history = models.JSONField(default=list, blank=True, db_index=True)