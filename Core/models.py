import os

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.core.files.storage import FileSystemStorage
from django.conf import settings

schema_storage = FileSystemStorage(location=os.path.join(settings.BASE_DIR, 'media', 'schemas'))

class LabStand(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    # Це показує, який Arduino підключений (наприклад, 'COM3' або '/dev/ttyUSB0')
    port = models.CharField(max_length=50, unique=True)
    is_busy = models.BooleanField(default=False)
    current_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    video_stream_url = models.URLField(max_length=200, blank=True, null=True)
    occupied_since = models.DateTimeField(null=True, blank=True)
    last_agent_heartbeat = models.DateTimeField(null=True, blank=True)
    installed_libraries = models.JSONField(default=list, blank=True)
    validation_rules = models.JSONField(default=dict, blank=True)
    schema_image = models.ImageField(upload_to='schemas/', blank=True, null=True, storage=schema_storage,
                                     help_text="Зображення електричної схеми стенду")


    @property
    def is_agent_online(self):
        """
        Вважаємо агента "онлайн", якщо останній пульс був протягом останніх 2 хвилин (120 секунд).
        """
        if not self.last_agent_heartbeat:
            return False

        # Поріг неактивності: 2 хвилини
        threshold = timezone.now() - timedelta(seconds=120)
        return self.last_agent_heartbeat > threshold

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
    # Встановлюємо 9600 як стандартне
    baud_rate = models.IntegerField(default=9600)
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


class LibraryJob(models.Model):
    """
    Модель, що представляє одне завдання на встановлення бібліотеки.
    """
    JOB_INSTALL = 'install'
    JOB_UNINSTALL = 'uninstall'
    JOB_TYPES = [
        (JOB_INSTALL, 'Встановлення'),
        (JOB_UNINSTALL, 'Видалення'),
    ]

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

    stand = models.ForeignKey(LabStand, on_delete=models.CASCADE, related_name='lib_jobs')
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    job_type = models.CharField(
        max_length=20,
        choices=JOB_TYPES,
        default=JOB_INSTALL
    )
    # Назва бібліотеки для встановлення
    library_name = models.CharField(max_length=100, blank=True, null=True)

    library_zip = models.FileField(upload_to='library_zips/', blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )

    output = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"LibJob #{self.id} for {self.stand.name} ({self.library_name})"

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import os

@receiver(post_save, sender=LibraryJob)
def auto_delete_file_on_completion(sender, instance, **kwargs):
    """
    Автоматично видаляє .zip файл з диска сервера,
    коли завдання завершується (успішно або з помилкою).
    """
    if instance.status in [LibraryJob.STATUS_COMPLETED, LibraryJob.STATUS_FAILED]:
        if instance.library_zip:
            if os.path.isfile(instance.library_zip.path):
                os.remove(instance.library_zip.path)
                print(f"🧹 [SERVER] Видалено використаний архів: {instance.library_zip.path}")

@receiver(post_delete, sender=LibraryJob)
def auto_delete_file_on_record_delete(sender, instance, **kwargs):
    """
    Видаляє файл з диска, якщо ми видаляємо сам запис про завдання з адмінки.
    """
    if instance.library_zip:
        if os.path.isfile(instance.library_zip.path):
            os.remove(instance.library_zip.path)
            print(f"🧹 [SERVER] Запис видалено, архів теж: {instance.library_zip.path}")