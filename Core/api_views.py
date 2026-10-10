from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from .linter import validate_code
# ⚠️ ПЕРЕКОНАЙТЕСЯ, ЩО ЦІ МОДЕЛІ ІМПОРТОВАНІ
from .models import FlashJob, LabStand, LibraryJob, CompileJob
from .serializers import FlashJobSerializer, LibraryJobSerializer, CompileJobSerializer


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

    def get_queryset(self):
        qs = super().get_queryset()
        stand = self.request.query_params.get("stand") or self.request.query_params.get("stand_id")
        if stand:
            qs = qs.filter(stand_id=stand)
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        ordering = self.request.query_params.get("ordering")
        if ordering:
            qs = qs.order_by(ordering)
        return qs


    # 🔽🔽🔽 2. ПЕРЕВИЗНАЧТЕ МЕТОД 'CREATE' 🔽🔽🔽
    def create(self, request, *args, **kwargs):
        code = request.data.get('code_to_flash')
        stand_id = request.data.get('stand')

        if not code or not stand_id:
            return Response({'error': 'Відсутній код або ID стенду'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Знаходимо стенд і його правила
            stand = LabStand.objects.get(pk=stand_id)
            rules = stand.validation_rules

            # Запускаємо валідацію ТІЛЬКИ якщо правила існують
            if rules:
                print(f"🔬 Запуск лінтера для стенду '{stand.name}' з правилами: {rules}")
                is_safe, message = validate_code(code, rules)

                if not is_safe:
                    # 3. БЛОКУЄМО ЗАПИТ, ЯКЩО НЕБЕЗПЕЧНО
                    print(f"🛑 НЕБЕЗПЕЧНИЙ КОД ЗАБЛОКОВАНО: {message}")
                    # Повертаємо помилку 400, яку побачить JavaScript
                    return Response({'error': f"Помилка валідації: {message}"}, status=status.HTTP_400_BAD_REQUEST)

            print("✅ Код пройшов валідацію.")

        except LabStand.DoesNotExist:
            return Response({'error': 'Стенд не знайдено'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # Ловимо будь-які помилки в самому лінтері
            return Response({'error': f'Внутрішня помилка лінтера: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 4. Якщо все безпечно, викликаємо оригінальний метод 'create'
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """
        Автоматично призначаємо поточного користувача при створенні нового завдання.
        """
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
        libraries_list = request.data.get('libraries')
        if libraries_list is not None:
            stand.installed_libraries = libraries_list
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
# =======================================================
# 4. VIEWSET ДЛЯ ЗАВДАНЬ ВСТАНОВЛЕННЯ БІБЛІОТЕК
# =======================================================

class LibraryJobViewSet(viewsets.ModelViewSet):
    """
    API endpoint для завдань встановлення бібліотек.
    """
    queryset = LibraryJob.objects.all().order_by('-created_at')
    serializer_class = LibraryJobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        stand = self.request.query_params.get("stand") or self.request.query_params.get("stand_id")
        if stand:
            qs = qs.filter(stand_id=stand)
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        ordering = self.request.query_params.get("ordering")
        if ordering:
            qs = qs.order_by(ordering)
        return qs


    def perform_create(self, serializer):
        """
        Автоматично призначаємо поточного користувача.
        """
        serializer.save(user=self.request.user)


class CompileJobViewSet(viewsets.ModelViewSet):
    """
    API endpoint для завдань "тільки компіляція".
    """
    queryset = CompileJob.objects.all().order_by('-created_at')
    serializer_class = CompileJobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        stand = self.request.query_params.get("stand") or self.request.query_params.get("stand_id")
        if stand:
            qs = qs.filter(stand_id=stand)
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        ordering = self.request.query_params.get("ordering")
        if ordering:
            qs = qs.order_by(ordering)
        return qs


    def create(self, request, *args, **kwargs):
        """
        Перевизначено для додавання валідації коду (лінтера).
        """
        code = request.data.get('code_to_compile')  # 1. Беремо 'code_to_compile'
        stand_id = request.data.get('stand')

        if not code or not stand_id:
            return Response({'error': 'Відсутній код або ID стенду'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 2. Перевіряємо правила безпеки стенду
            stand = LabStand.objects.get(pk=stand_id)
            rules = stand.validation_rules

            if rules:
                print(f"🔬(Compile) Запуск лінтера для стенду '{stand.name}' з правилами: {rules}")
                is_safe, message = validate_code(code, rules)

                if not is_safe:
                    print(f"🛑(Compile) НЕБЕЗПЕЧНИЙ КОД ЗАБЛОКОВАНО: {message}")
                    return Response({'error': f"Помилка валідації: {message}"}, status=status.HTTP_400_BAD_REQUEST)

            print("✅(Compile) Код пройшов валідацію.")

        except LabStand.DoesNotExist:
            return Response({'error': 'Стенд не знайдено'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'Внутрішня помилка лінтера: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 3. Якщо все безпечно, викликаємо оригінальний метод 'create'
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """
        Автоматично призначаємо поточного користувача.
        """
        serializer.save(user=self.request.user)


# В Core/api_views.py
# ... (всі імпорти, включаючи 'status', 'api_view', 'Response', 'CompileJob')

# ... (в кінці файлу, після CompileJobViewSet) ...

# =======================================================
# 6. API ДЛЯ СКАСУВАННЯ ЗАВДАНЬ
# =======================================================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_flash_job(request, pk):
    """
    Встановлює статус 'cancelling' для завдання FlashJob.
    """
    try:
        job = FlashJob.objects.get(pk=pk, user=request.user)
        if job.status in [FlashJob.STATUS_PENDING, FlashJob.STATUS_RUNNING]:
            job.status = FlashJob.STATUS_CANCELLING
            job.save()
            return Response({'status': 'cancellation_requested'}, status=status.HTTP_2_0_OK)
        return Response({'error': 'Job cannot be cancelled'}, status=status.HTTP_4_0_BAD_REQUEST)
    except FlashJob.DoesNotExist:
        return Response(status=status.HTTP_4_0_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_compile_job(request, pk):
    """
    Встановлює статус 'cancelling' для завдання CompileJob.
    """
    try:
        job = CompileJob.objects.get(pk=pk, user=request.user)
        if job.status in [CompileJob.STATUS_PENDING, CompileJob.STATUS_RUNNING]:
            job.status = CompileJob.STATUS_CANCELLING
            job.save()
            return Response({'status': 'cancellation_requested'}, status=status.HTTP_2_0_OK)
        return Response({'error': 'Job cannot be cancelled'}, status=status.HTTP_4_0_BAD_REQUEST)
    except CompileJob.DoesNotExist:
        return Response(status=status.HTTP_4_0_NOT_FOUND)
