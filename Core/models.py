from django.db import models
from django.contrib.auth.models import User

class LabStand(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    # Це показує, який Arduino підключений (наприклад, 'COM3' або '/dev/ttyUSB0')
    port = models.CharField(max_length=50, unique=True)
    is_busy = models.BooleanField(default=False)
    current_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    video_stream_url = models.URLField(max_length=200, blank=True, null=True)
    occupied_since = models.DateTimeField(null=True, blank=True)


    def __str__(self):
        return self.name

class FlashJob(models.Model):
    """
    Модель, що представляє одне завдання на прошивку стенду.
    """
    STATUS_PENDING = 'pending'
    STATUS_RUNNING = 'running'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Очікування'),
        (STATUS_RUNNING, 'Виконується'),
        (STATUS_COMPLETED, 'Завершено'),
        (STATUS_FAILED, 'Помилка'),
    ]

    # До якого стенду це завдання?
    stand = models.ForeignKey(LabStand, on_delete=models.CASCADE, related_name='jobs')
    # Який користувач його створив?
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Код, який потрібно прошити
    code_to_flash = models.TextField()

    # Поточний статус
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )

    # Результат виконання (вивід з arduino-cli або монітора порту)
    output = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Job #{self.id} for {self.stand.name} ({self.status})"