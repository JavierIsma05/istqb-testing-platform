import json

from django import forms

from apps.core.codes import next_code
from apps.testplans.models import TestPlan

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
        test_plan_id = self.data.get('test_plan') if self.is_bound else self.instance.test_plan_id
        project_id = None
        if test_plan_id:
            project_id = TestPlan.objects.filter(pk=test_plan_id).values_list('project_id', flat=True).first()
        queryset = TestCase.objects.filter(test_plan__project_id=project_id) if project_id else TestCase.objects.none()
        self.fields['code'].required = False
        self.fields['code'].disabled = True
        self.fields['code'].initial = self.instance.code or next_code(queryset, 'TC')
        self.fields['code'].widget.attrs.update({
            'placeholder': 'TC-000',
            'readonly': 'readonly',
            'data-default-code': 'TC-000',
        })
        self.fields['test_plan'].widget.attrs.update({
            'data-code-target': self.fields['code'].widget.attrs.get('id', 'id_code'),
            'data-next-codes': json.dumps({
                str(test_plan.pk): next_code(
                    TestCase.objects.filter(test_plan__project_id=test_plan.project_id),
                    'TC',
                )
                for test_plan in TestPlan.objects.only('id', 'project_id')
            }),
        })
        help_texts = {
            'test_plan': 'Plan de pruebas donde se ejecutara o controlara este caso.',
            'requirement': 'Requisito cubierto por el caso; ayuda a medir trazabilidad.',
            'priority': 'Importancia del caso para ordenar la ejecucion.',
            'technique': 'Tecnica ISTQB usada para disenar el caso, como particion de equivalencia o valores limite.',
            'level': 'Nivel donde aplica el caso: componente, integracion, sistema o aceptacion.',
            'status': 'Estado de preparacion o ejecucion del caso.',
        }
        for name, help_text in help_texts.items():
            self.fields[name].help_text = help_text
            self.fields[name].widget.attrs['data-help'] = help_text
