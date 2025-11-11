import os
from django.core.wsgi import get_wsgi_application
from django.conf import settings
from whitenoise import WhiteNoise

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Labaratoria.settings')

# 1. Беремо звичайний додаток
application = get_wsgi_application()

# 2. Обгортаємо його в WhiteNoise для роздачі static/media
application = WhiteNoise(application, root=settings.STATIC_ROOT)
application.add_files(settings.MEDIA_ROOT, prefix=settings.MEDIA_URL)
