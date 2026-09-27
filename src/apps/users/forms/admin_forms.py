from django import forms

from ..models import User


class AdminUserForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Contraseña',
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        help_text='Déjala vacía al editar para conservar la contraseña actual.',
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'role', 'is_active')
        labels = {
            'email': 'Correo institucional',
            'first_name': 'Nombres',
            'last_name': 'Apellidos',
            'role': 'Rol',
            'is_active': 'Usuario activo',
        }
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_email(self):
        return self.cleaned_data['email'].strip().lower()

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get('password1')
        password2 = cleaned.get('password2')
        if password1 or password2:
            if password1 != password2:
                self.add_error('password2', 'Las contraseñas no coinciden.')
            if password1 and len(password1) < 8:
                self.add_error('password1', 'La contraseña debe tener al menos 8 caracteres.')
        elif not self.instance.pk:
            self.add_error('password1', 'La contraseña es obligatoria al crear un usuario.')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password1')
        if password:
            user.set_password(password)
        if user.role == User.Roles.ADMIN:
            user.is_staff = True
        else:
            user.is_staff = False
            user.is_superuser = False
        if commit:
            user.save()
        return user
