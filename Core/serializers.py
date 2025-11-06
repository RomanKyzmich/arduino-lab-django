from rest_framework import serializers
from .models import FlashJob, LabStand

class FlashJobSerializer(serializers.ModelSerializer):
    """
    Серіалізатор для моделі FlashJob.
    Перетворює її в JSON і назад.
    """

    # Ми хочемо бачити ім'я користувача, а не його ID
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = FlashJob
        # Вказуємо, які поля ми хочемо бачити в API
        fields = [
            'id',
            'stand',
            'user_username',
            'status',
            'code_to_flash', # Це поле потрібне агенту
            'output',        # Це поле агент буде оновлювати
            'created_at'
        ]

        # Вказуємо, які поля агент не може редагувати напряму
        read_only_fields = ['output', 'created_at', 'user_username']