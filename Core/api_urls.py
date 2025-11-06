from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

# Створюємо "роутер" (маршрутизатор)
router = DefaultRouter()

# Реєструємо наш ViewSet.
# DRF автоматично створить URL-адреси для 'jobs'
router.register(r'jobs', api_views.FlashJobViewSet, basename='job')

# Наші URL-адреси API
urlpatterns = [
    path('', include(router.urls)),
]