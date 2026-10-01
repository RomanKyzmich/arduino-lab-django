import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.sessions import SessionMiddlewareStack
from django.core.handlers.asgi import ASGIHandler

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Labaratoria.settings')

django.setup()

from Core.token_auth import TokenAuthMiddleware
import Core.routing
from Labaratoria.wsgi import application as wsgi_app_with_whitenoise  # можеш залишити, якщо потрібно для Gunicorn WSGI

application = ProtocolTypeRouter({
    # ✅ ASGIHandler не приймає аргументів
    "http": ASGIHandler(),

    "websocket": SessionMiddlewareStack(
        TokenAuthMiddleware(
            AuthMiddlewareStack(
                URLRouter(Core.routing.websocket_urlpatterns)
            )
        )
    ),
})
