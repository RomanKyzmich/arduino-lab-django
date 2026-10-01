from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
import io
import base64
import qrcode
import pyotp
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm

# Імпортуємо нашу модель
from .models import LabStand, Profile


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
def setup_2fa_view(request):
    """Генерує QR-код для сканування в додатку Google Authenticator"""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    secret = profile.generate_otp_secret()

    # Створюємо URI для Google Authenticator
    totp = pyotp.TOTP(secret)
    otp_uri = totp.provisioning_uri(
        name=request.user.email or request.user.username,
        issuer_name="ArduinoLab"
    )

    # Генеруємо зображення QR-коду
    img = qrcode.make(otp_uri)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    if request.method == 'POST':
        code = request.POST.get('otp_code', '').strip()
        if totp.verify(code):
            profile.is_2fa_enabled = True
            profile.save()
            messages.success(request, "2FA успішно активовано!")
            return redirect('stand-list')
        else:
            messages.error(request, "Невірний код. Спробуйте ще раз.")

    return render(request, 'core/setup_2fa.html', {
        'qr_b64': qr_b64,
        'secret': secret,
        'is_enabled': profile.is_2fa_enabled
    })


def custom_login_view(request):
    """Перший крок: перевірка логіна та пароля"""
    if request.user.is_authenticated:
        return redirect('stand-list')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            profile, _ = Profile.objects.get_or_create(user=user)

            if profile.is_2fa_enabled:
                # Якщо 2FA увімкнено — зберігаємо ID і йдемо на перевірку коду
                request.session['pre_2fa_user_id'] = user.id
                return redirect('verify-2fa')
            else:
                auth_login(request, user)
                return redirect('stand-list')
    else:
        form = AuthenticationForm(request)

    return render(request, 'core/login.html', {'form': form})


def verify_2fa_view(request):
    """Другий крок: перевірка 6-значного коду з Google Authenticator"""
    user_id = request.session.get('pre_2fa_user_id')
    if not user_id:
        return redirect('login')

    user = get_object_or_404(User, id=user_id)
    profile = user.profile

    if request.method == 'POST':
        code = request.POST.get('otp_code', '').strip()
        totp = pyotp.TOTP(profile.otp_secret)

        if totp.verify(code):
            del request.session['pre_2fa_user_id']
            auth_login(request, user)
            return redirect('stand-list')
        else:
            messages.error(request, "Невірний код із Google Authenticator.")

    return render(request, 'core/verify_2fa.html')

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
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'core/signup.html'
