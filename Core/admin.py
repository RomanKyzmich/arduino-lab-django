from django.contrib import admin
from .models import LabStand, FlashJob, LibraryJob


# Створюємо клас, щоб налаштувати вигляд моделі в адмінці
class LabStandAdmin(admin.ModelAdmin):
    # Які поля показувати у списку всіх стендів
    list_display = ('name', 'port', 'is_busy', 'video_stream_url')

    # Які поля показувати на сторінці редагування
    # (ми просто перелічуємо їх, щоб контролювати порядок)
    fields = ('name', 'description', 'port', 'video_stream_url', 'schema_image', 'validation_rules', 'is_busy', 'current_user')

# Реєструємо модель, але тепер з нашими налаштуваннями
admin.site.register(LabStand, LabStandAdmin)
admin.site.register(FlashJob)
admin.site.register(LibraryJob)