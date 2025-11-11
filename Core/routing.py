# В файлі Core/routing.py

from django.urls import re_path
from . import consumers # Ми створимо цей файл наступним

websocket_urlpatterns = [
    # Ми будемо підключатися до URL: ws://.../ws/serial/<ID_стенду>/
    re_path(r'ws/serial/(?P<stand_id>\d+)/$', consumers.SerialConsumer.as_asgi()),
]