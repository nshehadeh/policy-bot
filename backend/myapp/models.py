from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class ChatHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    setting_name = models.CharField(max_length=100)
    setting_value = models.CharField(max_length=100)