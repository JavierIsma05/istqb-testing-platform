from django import forms

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
        self.fields['members'].help_text = 'Selecciona estudiantes y docentes vinculados al proyecto.'
