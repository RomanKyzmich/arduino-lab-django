# В файлі Core/consumers.py
import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync


class SerialConsumer(WebsocketConsumer):

    def connect(self):
        # Отримуємо ID стенду з URL (див. routing.py)
        self.stand_id = self.scope['url_route']['kwargs']['stand_id']
        self.stand_group_name = f'stand_{self.stand_id}'
        self.user = self.scope['user']

        # 1. Перевірка, чи користувач автентифікований
        if not self.user.is_authenticated:
            self.close()
            return

        # 2. Додаємо цей WebSocket до "групи" (кімнати)
        # Це дозволить Агенту надсилати дані всім, хто "слухає" цей стенд
        async_to_sync(self.channel_layer.group_add)(
            self.stand_group_name,
            self.channel_name
        )

        # 3. Приймаємо з'єднання
        self.accept()
        print(f"WebSocket: Користувач {self.user.username} підключився до стенду {self.stand_id}")

    def disconnect(self, close_code):
        # Виходимо з групи
        async_to_sync(self.channel_layer.group_discard)(
            self.stand_group_name,
            self.channel_name
        )
        print(f"WebSocket: Користувач відключився зі стенду {self.stand_id}")

    # Ця функція буде викликана, коли ми отримаємо повідомлення З БРАУЗЕРА
    def receive(self, text_data):
        print(f"WebSocket: Отримано від {self.user.username}: {text_data}")

        # 4. Пересилаємо повідомлення з браузера в "групу"
        # Агент (який теж буде в цій групі) отримає це повідомлення
        async_to_sync(self.channel_layer.group_send)(
            self.stand_group_name,
            {
                'type': 'serial_message',  # Назва функції-обробника
                'message': text_data,
                'sender': 'user'  # Вказуємо, що це від користувача
            }
        )

    # Ця функція буде викликана, коли АГЕНТ надішле повідомлення в групу
    def serial_message(self, event):
        message = event['message']
        sender = event.get('sender', 'agent')

        # 5. Пересилаємо повідомлення в браузер (користувачу)
        # Ми НЕ хочемо надсилати користувачу його ж власні повідомлення
        if sender == 'agent':
            self.send(text_data=json.dumps({
                'message': message
            }))