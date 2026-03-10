import logging

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib import messages

from .models import Usuario

logger = logging.getLogger(__name__)


def login_view(request):
    """Vista para iniciar sesión con email y contraseña."""
    if request.user.is_authenticated:
        return redirect('home')

    error = None
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        if not email or not password:
            error = 'Por favor introduce tu email y contraseña.'
        else:
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                logger.info('Login exitoso: %s', email)
                return redirect('home')
            else:
                error = 'Email o contraseña incorrectos.'
                logger.warning('Intento de login fallido para: %s', email)

    return render(request, 'usuarios/login.html', {'error': error})


@login_required
def logout_view(request):
    """Cierra la sesión del usuario. Solo acepta POST para protección CSRF."""
    if request.method == 'POST':
        logger.info('Logout: %s', request.user.email)
        logout(request)
    return redirect('login')


@login_required
def cambio_password(request):
    """Vista para cambiar la contraseña del usuario autenticado."""
    error = None

    if request.method == 'POST':
        old_password = request.POST.get('old_password', '')
        new_password = request.POST.get('new_password', '')
        new_password_conf = request.POST.get('new_password_conf', '')

        user = request.user

        if not user.check_password(old_password):
            error = 'La contraseña actual es incorrecta.'
        elif len(new_password) < 8:
            error = 'La nueva contraseña debe tener al menos 8 caracteres.'
        elif new_password != new_password_conf:
            error = 'Las contraseñas nuevas no coinciden.'
        else:
            user.set_password(new_password)
            user.save()
            logger.info('Contraseña cambiada para: %s', user.email)
            logout(request)
            messages.success(request, 'Contraseña cambiada correctamente. Inicia sesión de nuevo.')
            return redirect('login')

    return render(request, 'usuarios/cambio_password.html', {'error': error})


def reset_password(request):
    """Envía un email con el enlace de recuperación de contraseña."""
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                email_template_name='registration/password_reset_email.html',
                subject_template_name='registration/password_reset_subject.txt',
            )
            messages.info(
                request,
                'Si el email existe en nuestra base de datos, recibirás un enlace para restablecer tu contraseña.'
            )
            return redirect('login')
    else:
        form = PasswordResetForm()

    return render(request, 'usuarios/reset_password.html', {'form': form})
