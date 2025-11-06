from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone

# ⚠️ ПЕРЕКОНАЙТЕСЯ, ЩО ЦІ МОДЕЛІ ІМПОРТОВАНІ
from .models import FlashJob, LabStand
from .serializers import FlashJobSerializer


# =======================================================
# 1. VIEWSET ДЛЯ ЗАВДАНЬ (FLASHJOB)
# =======================================================

class FlashJobViewSet(viewsets.ModelViewSet):
    """
    API endpoint, що дозволяє переглядати та редагувати "Завдання на прошивку".
    """
    queryset = FlashJob.objects.all().order_by('-created_at')
    serializer_class = FlashJobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """
        Автоматично призначаємо поточного користувача при створенні нового завдання.
        """
        # self.request.user - це залогінений користувач
        serializer.save(user=self.request.user)


# =======================================================
# 2. VIEW ДЛЯ ПУЛЬСУ АГЕНТА (AGENT HEARTBEAT)
# =======================================================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def agent_heartbeat_view(request):
    """
    Агент надсилає сюди POST-запит, щоб повідомити, що він живий,
    оновлюючи час 'last_agent_heartbeat'.
    """
    # Ми очікуємо ID стенду, який агент обслуговує
    stand_id = request.data.get('stand_id')
    if not stand_id:
        return Response({'error': 'stand_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        stand = LabStand.objects.get(pk=stand_id)

        # Оновлення часу останнього "пульсу"
        stand.last_agent_heartbeat = timezone.now()
        stand.save()

        return Response({'status': 'heartbeat_received', 'stand_id': stand.id})

    except LabStand.DoesNotExist:
        return Response({'error': f'Stand {stand_id} not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_ERROR)


# =======================================================
# 3. VIEW ДЛЯ ПУЛЬСУ КОРИСТУВАЧА (USER HEARTBEAT)
# =======================================================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def stand_heartbeat_view(request):
    """
    "Пульс" від браузера користувача.
    Оновлює час 'occupied_since', щоб запобігти автоматичному звільненню.
    """
    try:
        # Знаходимо стенд, який зараз займає ЦЕЙ користувач
        stand = LabStand.objects.get(
            is_busy=True,
            current_user=request.user
        )

        # Оновлюємо час останньої активності
        stand.occupied_since = timezone.now()
        stand.save()

        return Response({'status': 'heartbeat_received'})

    except LabStand.DoesNotExist:
        # Якщо користувач не займає жодного стенду, це нормально
        return Response({'status': 'no_active_stand'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_ERROR)