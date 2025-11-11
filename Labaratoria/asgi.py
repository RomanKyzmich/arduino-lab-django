# В файлі Labaratoria/asgi.py

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import Core.routing # <--- Імпортуємо наші майбутні WebSocket-маршрути

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Labaratoria.settings')

# Отримуємо звичайний HTTP-додаток
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    # 1. Обробка HTTP-запитів (так само, як і раніше)
    "http": django_asgi_app,

    # 2. Обробка WebSocket-запитів
    "websocket": AuthMiddlewareStack( # Дозволяє нам бачити 'user' у WebSocket
        URLRouter(
            Core.routing.websocket_urlpatterns # Вказуємо, де шукати маршрути
        )
    ),
})