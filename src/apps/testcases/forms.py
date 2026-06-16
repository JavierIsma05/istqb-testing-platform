import json

from django import forms

from apps.core.codes import next_code
from apps.core.permissions import visible_projects_for
from apps.requirements.models import Requirement
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
            'test_data',
            'steps',
            'expected_result',
            'version',
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
            'test_data': 'Datos de Prueba',
            'steps': 'Pasos de Ejecución',
            'expected_result': 'Resultado Esperado',
            'version': 'Versión',
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
            'test_data': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Usuarios, entradas y datos necesarios para ejecutar el caso', 'rows': 3}
            ),
            'steps': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Abrir login => Se muestra el formulario\nIngresar credenciales => Los datos son aceptados',
                    'rows': 5,
                }
            ),
            'expected_result': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Descripción del resultado esperado', 'rows': 3}
            ),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'version': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1.0'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            visible_projects = visible_projects_for(user)
            self.fields['test_plan'].queryset = TestPlan.objects.filter(project__in=visible_projects).order_by(
                'project__name',
                'name',
            )
        self.fields['requirement'].required = True
        self.fields['version'].required = False
        self.fields['version'].initial = self.instance.version or '1.0'
        test_plan_id = self.data.get('test_plan') if self.is_bound else self.instance.test_plan_id
        if not test_plan_id and not self.is_bound:
            first_plan = self.fields['test_plan'].queryset.order_by('project__name', 'name').first()
            if first_plan:
                test_plan_id = first_plan.pk
                self.fields['test_plan'].initial = first_plan.pk
        project_id = None
        if test_plan_id:
            project_id = TestPlan.objects.filter(pk=test_plan_id).values_list('project_id', flat=True).first()
        self.fields['requirement'].queryset = (
            self.fields['requirement'].queryset.filter(project_id=project_id)
            if project_id
            else self.fields['requirement'].queryset.none()
        )
        queryset = TestCase.objects.filter(test_plan__project_id=project_id) if project_id else TestCase.objects.none()
        self.fields['code'].required = False
        self.fields['code'].disabled = True
        self.fields['code'].initial = self.instance.code or next_code(queryset, 'TC')
        self.fields['code'].widget.attrs.update({
            'placeholder': 'TC-000',
            'readonly': 'readonly',
            'data-default-code': 'TC-000',
        })
        available_plans = self.fields['test_plan'].queryset.only('id', 'project_id')
        self.fields['test_plan'].widget.attrs.update({
            'data-code-target': self.fields['code'].widget.attrs.get('id', 'id_code'),
            'data-requirement-target': self.fields['requirement'].widget.attrs.get('id', 'id_requirement'),
            'data-requirements-by-plan': json.dumps({
                str(test_plan.pk): [
                    {
                        'value': requirement.pk,
                        'label': str(requirement),
                    }
                    for requirement in Requirement.objects.filter(project_id=test_plan.project_id).order_by('code')
                ]
                for test_plan in available_plans
            }),
            'data-next-codes': json.dumps({
                str(test_plan.pk): next_code(
                    TestCase.objects.filter(test_plan__project_id=test_plan.project_id),
                    'TC',
                )
                for test_plan in available_plans
            }),
        })
        self.fields['requirement'].empty_label = 'Selecciona un requisito'
        help_texts = {
            'test_plan': 'Plan de pruebas donde se ejecutara o controlara este caso.',
            'requirement': 'Requisito cubierto por el caso; ayuda a medir trazabilidad.',
            'test_data': 'Datos concretos que deben usarse durante la ejecucion.',
            'steps': 'Escribe un paso por linea con el formato Accion => Resultado esperado.',
            'version': 'Version del caso aplicable a la version actual del proyecto.',
            'priority': 'Importancia del caso para ordenar la ejecucion.',
            'technique': 'Tecnica ISTQB usada para disenar el caso, como particion de equivalencia o valores limite.',
            'level': 'Nivel donde aplica el caso: componente, integracion, sistema o aceptacion.',
            'status': 'Estado de preparacion o ejecucion del caso.',
        }
        for name, help_text in help_texts.items():
            self.fields[name].help_text = help_text
            self.fields[name].widget.attrs['data-help'] = help_text

    def clean_steps(self):
        steps = (self.cleaned_data.get('steps') or '').strip()
        parsed_steps = []
        for number, line in enumerate(steps.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            if '=>' not in line:
                raise forms.ValidationError(
                    f'El paso {number} debe usar el formato Accion => Resultado esperado.'
                )
            action, expected = (part.strip() for part in line.split('=>', 1))
            if not action or not expected:
                raise forms.ValidationError(f'Completa la accion y el resultado esperado del paso {number}.')
            parsed_steps.append({'number': len(parsed_steps) + 1, 'action': action, 'expected_result': expected})
        if not parsed_steps:
            raise forms.ValidationError('Registra al menos un paso de ejecucion.')
        self.parsed_steps = parsed_steps
        return steps

    def clean_version(self):
        return (self.cleaned_data.get('version') or '').strip() or '1.0'

    def clean(self):
        cleaned_data = super().clean()
        test_plan = cleaned_data.get('test_plan')
        requirement = cleaned_data.get('requirement')
        if test_plan and requirement and test_plan.project_id != requirement.project_id:
            self.add_error('requirement', 'El requisito debe pertenecer al proyecto del plan seleccionado.')
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.steps_data = getattr(self, 'parsed_steps', [])
        if commit:
            instance.save()
            self.save_m2m()
        return instance
