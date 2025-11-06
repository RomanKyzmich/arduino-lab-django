from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

# Імпортуємо нашу модель
from .models import LabStand


@login_required
def stand_list_view(request):
    """
    Показує список всіх стендів.
    Також розраховує 'stale_threshold' для логіки "застарілих" замків.
    """
    stands = LabStand.objects.all()

    # Розраховуємо "пороговий" час (все, що старіше за це - застаріле)
    stale_threshold = timezone.now() - timedelta(minutes=settings.STAND_AUTO_RELEASE_MINUTES)

    context = {
        'stands': stands,
        'stale_threshold': stale_threshold  # Передаємо в шаблон
    }
    return render(request, 'core/stand_list.html', context)


@login_required
def stand_detail_view(request, pk):
    """
    Показує сторінку одного стенду.
    Обробляє логіку "захоплення", "оновлення замка" та "звільнення застарілого".
    """
    stand = get_object_or_404(LabStand, pk=pk)
    is_owner = (stand.current_user == request.user)

    # 1. Перевіряємо, чи стенд зайнятий кимось іншим
    if stand.is_busy and not is_owner:

        # 2. Розраховуємо час, коли "замок" застаріє
        timeout_duration = timedelta(minutes=settings.STAND_AUTO_RELEASE_MINUTES)

        # Перевіряємо, чи пройшов час (якщо occupied_since взагалі є)
        if stand.occupied_since and (timezone.now() - stand.occupied_since) > timeout_duration:
            # ЗАМОК ЗАСТАРІВ!
            messages.info(request,
                          f"Стенд '{stand.name}' був автоматично звільнений від {stand.current_user.username} через неактивність.")
            # Ми очищуємо стенд, і логіка нижче його захопить
            stand.is_busy = False
            stand.current_user = None
            stand.occupied_since = None
            stand.save()  # Зберігаємо "звільнення"

        else:
            # ЗАМОК СВІЖИЙ. Блокуємо доступ.
            messages.warning(request, f"Стенд '{stand.name}' наразі зайнятий {stand.current_user.username}.")
            return redirect('stand-list')

    # 3. Якщо стенд вільний, або ми його щойно звільнили,
    #    або ми вже були його власником - "захоплюємо" або "оновлюємо" замок.
    stand.is_busy = True
    stand.current_user = request.user
    stand.occupied_since = timezone.now()  # Встановлюємо або оновлюємо час!
    stand.save()

    # 4. Все добре, показуємо сторінку
    context = {
        'stand': stand
    }
    return render(request, 'core/stand_detail.html', context)


@login_required
def release_stand_view(request, pk):
    """
    Обробляє натискання кнопки "Завершити роботу".
    Звільняє стенд, якщо користувач є його власником.
    """
    stand = get_object_or_404(LabStand, pk=pk)

    # Перевіряємо, чи користувач є "власником" стенду
    if stand.current_user == request.user:
        stand.is_busy = False
        stand.current_user = None
        stand.occupied_since = None  # Очищуємо час
        stand.save()
        messages.success(request, f"Ви завершили роботу зі стендом '{stand.name}'.")
    else:
        messages.error(request, "Ви не можете звільнити стенд, який ви не займали.")

    # У будь-якому випадку, повертаємо користувача на головну сторінку
    return redirect('stand-list')


class SignUpView(generic.CreateView):
    """
    Сторінка реєстрації користувачів.
    """
    form_class = UserCreationForm
    success_url = reverse_lazy('login')  # Куди перекинути юзера після успішної реєстрації
    template_name = 'core/signup.html'  # Який шаблон використовувати