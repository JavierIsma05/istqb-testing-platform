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
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = 'Contrasena'
        self.fields['password2'].label = 'Confirmar contrasena'
        self.fields['password1'].widget.attrs.update({'class': 'form-control form-control-lg'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control form-control-lg'})

    def clean_email(self):
        email = self.cleaned_data['email']
        domain = email.split('@')[-1].lower()
        public_domains = {
            'gmail.com',
            'hotmail.com',
            'outlook.com',
            'yahoo.com',
            'icloud.com',
            'live.com',
        }

        if domain in public_domains:
            raise forms.ValidationError('Usa un correo institucional, no un correo personal.')

        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Roles.STUDENT
        if commit:
            user.save()
        return user
