from rest_framework import viewsets, permissions
from .models import FlashJob
from .serializers import FlashJobSerializer

class FlashJobViewSet(viewsets.ModelViewSet):
    """
    API endpoint, що дозволяє переглядати та редагувати "Завдання на прошивку".
    """
    # Які дані показувати: всі завдання, найновіші спочатку
    queryset = FlashJob.objects.all().order_by('-created_at')

    # Який серіалізатор використовувати (наш "перекладач")
    serializer_class = FlashJobSerializer

    # Хто може це бачити: Тільки аутентифіковані користувачі
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """
        Автоматично призначаємо поточного користувача при створенні нового завдання.
        """
        # self.request.user - це залогінений користувач
        serializer.save(user=self.request.user)