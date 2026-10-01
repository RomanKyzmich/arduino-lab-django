from pathlib import Path
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


def get_allowed_emails():
    """Зчитує дозволені email із файлу allowed_emails.txt"""
    file_path = Path(settings.BASE_DIR) / 'emails.txt'
    if not file_path.exists():
        return set()
    with open(file_path, 'r', encoding='utf-8') as f:
        return {
            line.strip().lower()
            for line in f
            if line.strip() and not line.startswith('#')
        }


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="Електронна пошта",
        help_text="Обов'язкове поле. Вкажіть вашу пошту зі списку дозволених."
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        allowed = get_allowed_emails()

        if email not in allowed:
            raise ValidationError(
                "Реєстрація дозволена лише для поштових адрес із затвердженого списку."
            )

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                "Користувач із цією електронною адресою вже зареєстрований."
            )

        return email