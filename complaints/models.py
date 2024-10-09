from django.db import models
from users.models import User


class Responsible(models.Model):
    full_name = models.CharField(max_length=255)
    telegram_id = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.full_name


class Complaint(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    STATUS_CHOICES = [
        ('pending', 'Ожидает решения'),
        ('in_progress', 'В процессе решения'),
        ('resolved', 'Решено')
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    responsibles = models.ManyToManyField(Responsible, related_name='complaints')
    responsible_in_progress = models.ForeignKey(Responsible, null=True, blank=True, on_delete=models.SET_NULL,
                                                related_name='complaints_in_progress')

    def __str__(self):
        return f'Пользователь:{self.user} ID:{self.id} Время создания:{self.created_at}'
