from django import forms

from .models import Defect


class DefectForm(forms.ModelForm):
    class Meta:
        model = Defect
        fields = (
            'project',
            'execution',
            'code',
            'title',
            'description',
            'severity',
            'priority',
            'status',
            'assigned_to',
        )
        labels = {
            'project': 'Proyecto',
            'execution': 'Ejecución relacionada',
            'code': 'Código',
            'title': 'Título del defecto',
            'description': 'Descripción',
            'severity': 'Severidad',
            'priority': 'Prioridad',
            'status': 'Estado',
            'assigned_to': 'Asignado a',
        }
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'execution': forms.Select(attrs={'class': 'form-select'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. DEF-001'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Error al cargar imágenes grandes'}),
            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Describe el defecto, pasos para reproducirlo y comportamiento esperado',
                    'rows': 4,
                }
            ),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['execution'].required = False
        self.fields['assigned_to'].required = False
