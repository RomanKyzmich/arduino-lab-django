
from django.contrib import admin
from .models import LabStand, FlashJob, LibraryJob

# Створюємо клас, щоб налаштувати вигляд моделі в адмінці
class LabStandAdmin(admin.ModelAdmin):
    
    # --- 🔽 1. ДОДАЙТЕ 'id' НА ПОЧАТОК 🔽 ---
    # Які поля показувати у списку всіх стендів
    list_display = ('id', 'name', 'port', 'is_busy', 'current_user', 'is_agent_online')

    # Які поля показувати на сторінці редагування
    fields = ('name', 'description', 'port', 'video_stream_url', 
              'schema_image', 'validation_rules', 'is_busy', 'current_user')

    # --- 🔽 2. ДОДАЙТЕ ЦЕЙ РЯДОК 🔽 ---
    # Це покаже поле ID (тільки для читання) на сторінці редагування
    readonly_fields = ('id',)

    # Додаємо фільтр, щоб легко знаходити стенди (бонус)
    list_filter = ('is_busy', )

# Реєструємо модель, але тепер з нашими налаштуваннями
admin.site.register(LabStand, LabStandAdmin)

# Реєструємо інші моделі (тут нічого не змінюємо)
admin.site.register(FlashJob)
admin.site.register(LibraryJob)
