from django import forms

from apps.core.codes import next_code

from .models import Project


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ('code', 'name', 'description', 'status', 'start_date', 'end_date', 'members')
        labels = {
            'code': 'Código',
            'name': 'Nombre del proyecto',
            'description': 'Descripción',
            'status': 'Estado',
            'start_date': 'Fecha de inicio',
            'end_date': 'Fecha de fin',
            'members': 'Miembros',
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
            'status': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'members': forms.SelectMultiple(attrs={'class': 'form-select project-members-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_date'].input_formats = ['%Y-%m-%d']
        self.fields['end_date'].input_formats = ['%Y-%m-%d']
        self.fields['members'].required = False
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
            'status': 'Indica si el proyecto esta planificado, activo, pausado o finalizado.',
            'start_date': 'Fecha desde la que se planifica iniciar las actividades de prueba.',
            'end_date': 'Fecha estimada para cerrar las actividades principales del proyecto.',
            'members': 'Selecciona estudiantes y docentes vinculados al proyecto.',
        }
        for name, help_text in help_texts.items():
            self.fields[name].help_text = help_text
            self.fields[name].widget.attrs['data-help'] = help_text
