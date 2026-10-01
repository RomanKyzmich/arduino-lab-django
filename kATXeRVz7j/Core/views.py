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
    stand_to_occupy = get_object_or_404(LabStand, pk=pk)
    is_owner = (stand_to_occupy.current_user == request.user)

    # 1. Перевіряємо, чи стенд зайнятий кимось іншим
    if stand_to_occupy.is_busy and not is_owner:

        # 2. Розраховуємо час, коли "замок" застаріє
        timeout_duration = timedelta(minutes=settings.STAND_AUTO_RELEASE_MINUTES)

        if stand_to_occupy.occupied_since and (timezone.now() - stand_to_occupy.occupied_since) > timeout_duration:
            messages.info(request,
                          f"Стенд '{stand_to_occupy.name}' був автоматично звільнений від {stand_to_occupy.current_user.username} через неактивність.")
            stand_to_occupy.is_busy = False
            stand_to_occupy.current_user = None
            stand_to_occupy.occupied_since = None
            stand_to_occupy.save()  # Зберігаємо "звільнення"

        else:
            messages.warning(request,
                             f"Стенд '{stand_to_occupy.name}' наразі зайнятий {stand_to_occupy.current_user.username}.")
            return redirect('stand-list')

    # --- 🔽 ПОЧАТОК ВИПРАВЛЕННЯ (ЦЕ НОВИЙ КОД) 🔽 ---
    # 3. ЗВІЛЬНЯЄМО ВСІ ІНШІ СТЕНДИ, ЯКІ ЗАЙМАЄ ЦЕЙ КОРИСТУВАЧ
    # (Використовуємо .exclude(), щоб не звільнити той, на який ми зараз заходимо)

    other_stands = LabStand.objects.filter(
        current_user=request.user
    ).exclude(pk=stand_to_occupy.pk)

    if other_stands.exists():
        for stand in other_stands:
            print(f"Звільнення старого стенду {stand.name} для користувача {request.user.username}")
            stand.is_busy = False
            stand.current_user = None
            stand.occupied_since = None
            stand.save()
            messages.info(request, f"Ви автоматично звільнили стенд '{stand.name}', займаючи новий.")

    # --- 🔼 КІНЕЦЬ ВИПРАВЛЕННЯ 🔼 ---

    # 4. Все добре, "захоплюємо" або "оновлюємо" замок для поточного стенду.
    stand_to_occupy.is_busy = True
    stand_to_occupy.current_user = request.user
    stand_to_occupy.occupied_since = timezone.now()  # Встановлюємо або оновлюємо час!
    stand_to_occupy.save()

    context = {
        'stand': stand_to_occupy
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