from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()

router.register(r'jobs', api_views.FlashJobViewSet, basename='job')
router.register(r'lib-jobs', api_views.LibraryJobViewSet, basename='lib-job')
router.register(r'compile-jobs', api_views.CompileJobViewSet, basename='compile-job')
path('jobs/<int:pk>/cancel/', api_views.cancel_flash_job, name='cancel-flash-job'),
path('compile-jobs/<int:pk>/cancel/', api_views.cancel_compile_job, name='cancel-compile-job'),
urlpatterns = [
    path('', include(router.urls)),
    path('agent-heartbeat/', api_views.agent_heartbeat_view, name='agent-heartbeat'),
    path('heartbeat/', api_views.stand_heartbeat_view, name='stand-heartbeat'),
]
