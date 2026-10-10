from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages


class MandatoryTwoFactorMiddleware:
    """
    Блокує доступ до сайту авторизованим користувачам,
    доки вони не налаштують двофакторну автентифікацію.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            profile = getattr(request.user, 'profile', None)

            # Якщо профіль є, але 2FA ще не ввімкнено
            if profile and not profile.is_2fa_enabled:
                allowed_paths = [
                    reverse('setup-2fa'),
                    reverse('logout'),
                ]

                # Дозволяємо доступ до сторінки 2FA, виходу, адмінки та статики
                is_allowed = (
                        request.path in allowed_paths
                        or request.path.startswith('/admin/')
                        or request.path.startswith('/static/')
                        or request.path.startswith('/media/')
                )

                if not is_allowed:
                    messages.warning(
                        request,
                        "⚠️ Для початку роботи зі стендами необхідно обов'язково налаштувати двофакторну автентифікацію."
                    )
                    return redirect('setup-2fa')

        return self.get_response(request)