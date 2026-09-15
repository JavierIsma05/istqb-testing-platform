from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.authentication.forms.login_form import LoginForm
from apps.authentication.forms.register_form import RegisterForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm()

    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            user = authenticate(
                request,
                email=email,
                password=password
            )

            if user is not None:
                login(request, user)
                if not form.cleaned_data.get('remember_me'):
                    request.session.set_expiry(0)

                return redirect('dashboard')
            messages.error(request, 'Credenciales inválidas. Verifica tu correo y contraseña.')

    return render(
        request,
        'authentication/login.html',
        {'form': form}
    )


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = RegisterForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('dashboard')

    return render(
        request,
        'authentication/register.html',
        {'form': form}
    )


@login_required
@require_POST
def logout_view(request):
    logout(request)
    return redirect('login')
