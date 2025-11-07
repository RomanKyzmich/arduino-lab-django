from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

# Створюємо "роутер" (маршрутизатор)
router = DefaultRouter()

# Реєструємо наш ViewSet.
router.register(r'jobs', api_views.FlashJobViewSet, basename='job')
router.register(r'lib-jobs', api_views.LibraryJobViewSet, basename='lib-job')

# Наші URL-адреси API
urlpatterns = [
    path('', include(router.urls)),

    # 1. ПУЛЬС АГЕНТА (використовується скриптом agent.py)
    path('agent-heartbeat/', api_views.agent_heartbeat_view, name='agent-heartbeat'),

    # 2. ПУЛЬС КОРИСТУВАЧА (використовується JavaScript на сторінці стенду)
    path('heartbeat/', api_views.stand_heartbeat_view, name='stand-heartbeat'),
]
