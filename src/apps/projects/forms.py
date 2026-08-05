from django import forms

from apps.core.codes import next_code
from apps.core.forms import CurrentAcademicYearValidationMixin, current_year_date_attrs
from apps.users.models import User

from .models import Project


class ProjectForm(CurrentAcademicYearValidationMixin, forms.ModelForm):
    tutor = forms.ModelChoiceField(
        label='Docente tutor',
        required=False,
        queryset=User.objects.filter(role=User.Roles.TEACHER).order_by('first_name', 'last_name', 'email'),
        empty_label='-- Seleccionar docente --',
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Selecciona el docente registrado que tutorará el proyecto.',
    )

    class Meta:
        model = Project
        fields = ('code', 'name', 'description', 'start_date', 'end_date', 'tutor')
        labels = {
            'code': 'Código',
            'name': 'Nombre del proyecto',
            'description': 'Descripción',
            'start_date': 'Fecha de inicio',
            'end_date': 'Fecha de fin',
            'tutor': 'Docente tutor',
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
            'start_date': forms.DateInput(
                attrs=current_year_date_attrs({'class': 'form-control', 'type': 'date'}),
                format='%Y-%m-%d',
            ),
            'end_date': forms.DateInput(
                attrs=current_year_date_attrs({'class': 'form-control', 'type': 'date'}),
                format='%Y-%m-%d',
            ),
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
            'name': 'Escribe un nombre claro del sistema o módulo que será probado.',
            'description': 'Resume el objetivo, contexto y alcance general del proyecto.',
            'start_date': 'Fecha desde la que se planifica iniciar las actividades de prueba.',
            'end_date': 'Fecha estimada para cerrar las actividades principales del proyecto.',
            'tutor': 'Solo se listan los docentes registrados en la plataforma.',
        }
        for name, help_text in help_texts.items():
            self.fields[name].help_text = help_text
            self.fields[name].widget.attrs['data-help'] = help_text
