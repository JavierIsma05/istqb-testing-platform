from django import forms


class LoginForm(forms.Form):
    email = forms.EmailField(
        label='Correo Institucional',
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'estudiante@universidad.edu'
            }
        )
    )
    password = forms.CharField(
        label='Contrasena',
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control form-control-lg',
                'placeholder': '********'
            }
        )
    )
    remember_me = forms.BooleanField(
        label='Recordarme',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
