from django import forms

from .models import TestCase


class TestCaseModalForm(forms.ModelForm):
    class Meta:
        model = TestCase
        fields = (
            'test_plan',
            'requirement',
            'code',
            'title',
            'description',
            'priority',
            'technique',
            'level',
            'preconditions',
            'steps',
            'expected_result',
            'status',
        )
        labels = {
            'test_plan': 'Plan de Pruebas',
            'requirement': 'Requisito',
            'code': 'ID del Caso',
            'title': 'Título',
            'description': 'Descripción',
            'priority': 'Prioridad',
            'technique': 'Técnica ISTQB',
            'level': 'Nivel de Prueba',
            'preconditions': 'Precondiciones',
            'steps': 'Pasos de Ejecución',
            'expected_result': 'Resultado Esperado',
            'status': 'Estado',
        }
        widgets = {
            'test_plan': forms.Select(attrs={'class': 'form-select'}),
            'requirement': forms.Select(attrs={'class': 'form-select'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'TC-XXX'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título descriptivo del caso de prueba'}),
            'description': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Descripción detallada del caso de prueba', 'rows': 3}
            ),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'technique': forms.Select(attrs={'class': 'form-select'}),
            'level': forms.Select(attrs={'class': 'form-select'}),
            'preconditions': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Condiciones previas para ejecutar el caso', 'rows': 3}
            ),
            'steps': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': '1. Paso 1\n2. Paso 2\n3. Paso 3', 'rows': 4}
            ),
            'expected_result': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Descripción del resultado esperado', 'rows': 3}
            ),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['requirement'].required = False
