from django import forms

from apps.core.codes import next_code
from apps.users.models import User

from .models import Project


class ProjectForm(forms.ModelForm):
    tutor_email = forms.EmailField(
        label='Correo institucional del tutor',
        required=False,
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'tutor@universidad.edu',
            }
        ),
        help_text='Ingresa el correo del tutor registrado para vincularlo al proyecto.',
    )

    class Meta:
        model = Project
        fields = ('code', 'name', 'description', 'start_date', 'end_date', 'tutor_email')
        labels = {
            'code': 'Código',
            'name': 'Nombre del proyecto',
            'description': 'Descripción',
            'start_date': 'Fecha de inicio',
            'end_date': 'Fecha de fin',
            'tutor_email': 'Correo institucional del tutor',
        }
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. PRJ-001'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Sistema de Gestión Académica'}),
            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Describe el objetivo y alcance del proyecto',
                    'rows': 5,
                }
            ),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_date'].input_formats = ['%Y-%m-%d']
        self.fields['end_date'].input_formats = ['%Y-%m-%d']
        self.fields['code'].required = False
        self.fields['code'].disabled = True
        self.fields['code'].initial = self.instance.code or next_code(Project.objects.all(), 'PRJ')
        self.fields['code'].widget.attrs.update({
            'placeholder': 'PRJ-000',
            'readonly': 'readonly',
            'data-default-code': 'PRJ-000',
        })
        help_texts = {
            'code': 'Usa un identificador corto y unico para reconocer el proyecto en listados y reportes.',
            'name': 'Escribe un nombre claro del sistema o modulo que sera probado.',
            'description': 'Resume el objetivo, contexto y alcance general del proyecto.',
            'start_date': 'Fecha desde la que se planifica iniciar las actividades de prueba.',
            'end_date': 'Fecha estimada para cerrar las actividades principales del proyecto.',
            'tutor_email': 'Debe corresponder a un usuario con rol Docente/Tutor registrado.',
        }
        for name, help_text in help_texts.items():
            self.fields[name].help_text = help_text
            self.fields[name].widget.attrs['data-help'] = help_text

    def clean_tutor_email(self):
        tutor_email = self.cleaned_data.get('tutor_email')
        if not tutor_email:
            return ''

        try:
            tutor = User.objects.get(email__iexact=tutor_email)
        except User.DoesNotExist as exc:
            raise forms.ValidationError('No existe un tutor registrado con ese correo.') from exc

        if tutor.role != User.Roles.TEACHER:
            raise forms.ValidationError('El correo ingresado no pertenece a un tutor.')

        self.cleaned_data['tutor'] = tutor
        return tutor.email
