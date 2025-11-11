# В файлі Core/token_auth.py
from channels.middleware import BaseMiddleware
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async

@database_sync_to_async
def get_user_from_token(token_key):
    """
    Знаходить користувача за токеном.
    """
    try:
        return Token.objects.get(key=token_key).user
    except Token.DoesNotExist:
        return AnonymousUser()

class TokenAuthMiddleware(BaseMiddleware):
    """
    Middleware для WebSocket, який автентифікує за
    Authorization: Token <токен>
    """
    async def __call__(self, scope, receive, send):
        headers = dict(scope['headers'])

        # Шукаємо заголовок 'authorization' (у байтах)
        if b'authorization' in headers:
            try:
                # Отримуємо токен (напр. "Token 12345...")
                token_header = headers[b'authorization'].decode('utf-8')
                token_type, token_key = token_header.split()

                if token_type == 'Token':
                    # Знаходимо користувача в базі даних
                    scope['user'] = await get_user_from_token(token_key)
                    print(f"[TokenAuth] Агент автентифікований: {scope['user']}")

            except Exception as e:
                print(f"[TokenAuth] Помилка: {e}")
                scope['user'] = AnonymousUser()

        # Продовжуємо ланцюжок middleware
        return await super().__call__(scope, receive, send)
