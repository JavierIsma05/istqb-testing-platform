from django import forms
from django.contrib.auth.forms import UserCreationForm

from apps.users.models import User


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(
        label='Nombres',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg'})
    )
    last_name = forms.CharField(
        label='Apellidos',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg'})
    )
    email = forms.EmailField(
        label='Correo Institucional',
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'nombre@universidad.edu'
            }
        )
    )
    role = forms.ChoiceField(
        label='Rol',
        choices=User.Roles.choices,
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'})
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'role', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = 'Contrasena'
        self.fields['password2'].label = 'Confirmar contrasena'
        self.fields['password1'].widget.attrs.update({'class': 'form-control form-control-lg'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control form-control-lg'})
