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
        print(f"WebSocket: Користувач {self.user.username} (канал: {self.channel_name}) підключився до стенду {self.stand_id}")

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.stand_group_name,
            self.channel_name
        )
        print(f"WebSocket: Користувач (канал: {self.channel_name}) відключився зі стенду {self.stand_id}")

    # --- 🔽 ПОЧАТОК ВИПРАВЛЕННЯ 🔽 ---
    def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message', '')
        sender = data.get('sender', 'unknown')

        if sender == 'user':
            print(f"WS: Отримано від Користувача: {message.strip()}")
        elif sender == 'agent':
            print(f"WS: Отримано від Агента: {message.strip()}")

        # 1. Пересилаємо повідомлення ВСІМ у групі (включаючи нас самих)
        async_to_sync(self.channel_layer.group_send)(
            self.stand_group_name,
            {
                'type': 'serial_broadcast',  # <--- Назва функції-обробника
                'message': message,
                'sender': sender,
                'origin_channel': self.channel_name # <--- Хто відправив
            }
        )

    # Ця функція викликається у КОЖНОГО учасника групи
    def serial_broadcast(self, event):
        sender = event.get('sender')
        message = event.get('message')

        # 2. НЕ надсилаємо повідомлення назад тому, хто його відправив
        if self.channel_name == event.get('origin_channel'):
            return

        # 3. Визначаємо, кому відправити
        if sender == 'user':
            # Це повідомлення від Користувача, воно призначене для Агента.
            self.send(text_data=json.dumps({
                'message': message,
                'sender': 'user'
            }))

        elif sender == 'agent':
            # Це повідомлення від Агента, воно призначене для Користувача (браузера).
            self.send(text_data=json.dumps({
                'message': message
            }))
    # --- 🔼 КІНЕЦЬ ВИПРАВЛЕННЯ 🔼 ---
