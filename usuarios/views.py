from django.shortcuts import render, redirect

# Autenticacion
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password

# Create your views here.

def login_view(request):
    """Vista para hacer login en la aplicación"""
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)

        if user:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'usuarios/login.html', {'error': 'Usuario o password incorrecto'})

    return render(request, 'usuarios/login.html')


@login_required
def logout_view(request):
    """Vista para hacer logout en la aplicación"""
    logout(request)
    return redirect('login')


@login_required
def cambio_password(request):
    """Vista para cambiar contraseña"""

    if request.method == 'POST':
        old_password = request.POST['old_password']
        # Check de la contraseña introducida con la del usuario logado
        if check_password(old_password, request.user.password):
            new_password = request.POST['new_password']
            new_password_conf = request.POST['new_password_conf']
            if new_password != new_password_conf:
                return render(request, 'usuarios/cambio_password.html', {
                    'error': 'Las contraseñas no coinciden',
                })
            user = Usuario.objects.get(email=request.user.email)
            user.set_password(new_password)
            user.save()
            # Una vez salvada la nueva contraseña hacemos logout del usuario
            logout(request)
            return redirect('login')
        else:
            return render(request, 'usuarios/cambio_password.html', {
                'error': 'Contraseña incorrecta',
            })

def reset_password(request):
    """
    Vista para resetear la contraseña
    """
    
    if request.method == 'POST':
        email = request.POST["email"]
        if Usuario.objects.filter(email=email).exists():
            pass
            return redirect('login')
