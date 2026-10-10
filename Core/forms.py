from pathlib import Path
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


def get_allowed_emails():
    """Зчитує дозволені email із файлу allowed_emails.txt"""
    file_path = Path(settings.BASE_DIR) / 'allowed_emails.txt'
    if not file_path.exists():
        return set()
    with open(file_path, 'r', encoding='utf-8') as f:
        return {
            line.strip().lower()
            for line in f
            if line.strip() and not line.startswith('#')
        }


class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        label="Ім'я користувача (логін)",
        help_text="Обов'язкове поле. Лише літери, цифри та знаки @/./+/-/_."
    )
    email = forms.EmailField(
        label="Електронна пошта",
        required=True,
        help_text="Вкажіть вашу електронну адресу."  # 💡 Жодної згадки про білий список!
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Переклад полів пароля українською
        if 'password1' in self.fields:
            self.fields['password1'].label = "Пароль"
            self.fields['password1'].help_text = (
                "Пароль має містити щонайменше 8 символів і не бути надто простим."
            )
        if 'password2' in self.fields:
            self.fields['password2'].label = "Підтвердження пароля"
            self.fields['password2'].help_text = "Введіть той самий пароль ще раз для перевірки."

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Користувач із цією електронною адресою вже зареєстрований.")
        return email