from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync


class User(models.Model):
    full_name = models.CharField(max_length=255)
    room_number = models.CharField(max_length=10)
    pass_photo = models.ImageField(upload_to='pass_photos/')
    is_verified = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    telegram_id = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f'{self.full_name} (Комната {self.room_number})'


