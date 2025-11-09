import io
import os
import zipfile

from rest_framework import serializers
from .models import FlashJob, LabStand, LibraryJob


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
            'stand',
            'user_username',
            'status',
            'code_to_flash', # Це поле потрібне агенту
            'output',        # Це поле агент буде оновлювати
            'created_at',
            'baud_rate',
        ]

        # Вказуємо, які поля агент не може редагувати напряму
        read_only_fields = ['created_at', 'user_username']

class LibraryJobSerializer(serializers.ModelSerializer):
    """
    Серіалізатор для моделі LibraryJob.
    """
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = LibraryJob
        fields = [
            'id',
            'stand',
            'user_username',
            'status',
            'library_name',
            'library_zip',
            'job_type',
            'output',
            'created_at'
        ]
        # 'output' має бути доступним для запису агентом
        read_only_fields = ['created_at', 'user_username']

    def validate_library_zip(self, value):
        """
        Перевіряє .zip файл на наявність небезпечних шляхів (Path Traversal).
        """
        try:
            # Читаємо файл у пам'яті, не зберігаючи його на диск
            with zipfile.ZipFile(io.BytesIO(value.read()), 'r') as zip_ref:
                for file_info in zip_ref.infolist():
                    # 1. Перевірка на '..' (вихід з папки)
                    if ".." in file_info.filename:
                        raise serializers.ValidationError(
                            f"Помилка: .zip архів містить небезпечний шлях: '{file_info.filename}'")

                    # 2. Перевірка на абсолютні шляхи (напр. /etc/passwd або C:\)
                    if os.path.isabs(file_info.filename):
                        raise serializers.ValidationError(
                            f"Помилка: .zip архів містить небезпечний (абсолютний) шлях: '{file_info.filename}'")

            # Повертаємо файл на початок, щоб Django міг його зберегти
            value.seek(0)
            return value

        except zipfile.BadZipFile:
            raise serializers.ValidationError("Помилка: Завантажений файл не є валідним .zip архівом.")
        except Exception as e:
            raise serializers.ValidationError(f"Помилка валідації ZIP: {e}")