import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync


class SerialConsumer(WebsocketConsumer):
    def connect(self):
        self.stand_id = self.scope['url_route']['kwargs']['stand_id']
        self.stand_group_name = f'stand_{self.stand_id}'
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            print(f"WebSocket: Неавтентифіковане підключення до стенду {self.stand_id} ВІДХИЛЕНО.")
            self.close()
            return

        async_to_sync(self.channel_layer.group_add)(
            self.stand_group_name,
            self.channel_name
        )
        self.accept()
        print(f"WebSocket: Користувач {self.user.username} підключився до Serial стенду {self.stand_id}")

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.stand_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message', '')
        sender = data.get('sender', 'unknown')

        async_to_sync(self.channel_layer.group_send)(
            self.stand_group_name,
            {
                'type': 'serial_broadcast',
                'message': message,
                'sender': sender,
                'origin_channel': self.channel_name
            }
        )

    def serial_broadcast(self, event):
        if self.channel_name == event.get('origin_channel'):
            return

        sender = event.get('sender')
        message = event.get('message')

        if sender == 'user':
            self.send(text_data=json.dumps({'message': message, 'sender': 'user'}))
        elif sender == 'agent':
            self.send(text_data=json.dumps({'message': message}))


class VideoConsumer(WebsocketConsumer):
    def connect(self):
        self.stand_id = self.scope['url_route']['kwargs']['stand_id']
        self.video_group_name = f'stand_{self.stand_id}_video'

        # Визначаємо: агент чи глядач (в агента передається заголовок Authorization)
        headers = dict(self.scope.get('headers', []))
        self.is_agent = b'authorization' in headers

        async_to_sync(self.channel_layer.group_add)(
            self.video_group_name,
            self.channel_name
        )
        self.accept()

        if self.is_agent:
            print(f"[VideoWS] 📹 Відеоагент підключився до стенду {self.stand_id}")
        else:
            print(f"[VideoWS] 👤 Глядач зайшов на стенд {self.stand_id}. Відправляємо команду START агенту...")
            async_to_sync(self.channel_layer.group_send)(
                self.video_group_name,
                {
                    'type': 'video_command',
                    'command': 'start'
                }
            )

    def disconnect(self, close_code):
        if not getattr(self, 'is_agent', False):
            print(f"[VideoWS] 👤 Глядач вийшов зі стенду {self.stand_id}. Відправляємо STOP...")
            async_to_sync(self.channel_layer.group_send)(
                self.video_group_name,
                {
                    'type': 'video_command',
                    'command': 'stop'
                }
            )

        async_to_sync(self.channel_layer.group_discard)(
            self.video_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        try:
            data = json.loads(text_data)
            # Якщо агент прислав новий кадр
            if data.get('type') == 'frame':
                async_to_sync(self.channel_layer.group_send)(
                    self.video_group_name,
                    {
                        'type': 'video_broadcast',
                        'data': data.get('data'),
                        'origin_channel': self.channel_name
                    }
                )
        except Exception as e:
            print(f"[VideoWS] Помилка: {e}")

    def video_broadcast(self, event):
        # Відправляємо кадр ТІЛЬКИ глядачам (браузеру)
        if not getattr(self, 'is_agent', False) and self.channel_name != event.get('origin_channel'):
            self.send(text_data=json.dumps({
                'type': 'frame',
                'data': event.get('data')
            }))

    def video_command(self, event):
        # Відправляємо команди (start / stop) ТІЛЬКИ агенту
        if getattr(self, 'is_agent', False):
            self.send(text_data=json.dumps({
                'command': event.get('command')
            }))
