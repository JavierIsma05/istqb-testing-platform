from django import forms
from django.contrib.auth.forms import PasswordChangeForm

from apps.users.models import Profile


class ProfileEditForm(forms.ModelForm):
    first_name = forms.CharField(
        label='Nombres',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'given-name'}),
    )
    last_name = forms.CharField(
        label='Apellidos',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'family-name'}),
    )

    class Meta:
        model = Profile
        fields = ('first_name', 'last_name', 'bio', 'avatar')
        labels = {'bio': 'Biografía', 'avatar': 'Foto de perfil'}
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Escribe una breve descripción sobre ti...',
            }),
            'avatar': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/png,image/jpeg,image/webp',
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user is not None:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
        self.fields['bio'].required = False
        self.fields['avatar'].required = False

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar and avatar.size > 5 * 1024 * 1024:
            raise forms.ValidationError('La imagen no debe superar 5 MB.')
        return avatar

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user is not None:
            self.user.first_name = self.cleaned_data.get('first_name', '').strip()
            self.user.last_name = self.cleaned_data.get('last_name', '').strip()
            if commit:
                self.user.save(update_fields=['first_name', 'last_name'])
        if commit:
            profile.save()
        return profile


class ProfilePasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label='Contraseña actual',
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'current-password'}),
    )
    new_password1 = forms.CharField(
        label='Nueva contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )
    new_password2 = forms.CharField(
        label='Confirmar nueva contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )
