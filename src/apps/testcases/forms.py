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
            'custom_technique',
            'preconditions',
            'test_data',
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
            'custom_technique': 'Técnica personalizada',
            'preconditions': 'Precondiciones',
            'test_data': 'Datos de Prueba',
            'steps': 'Pasos de Ejecución',
            'expected_result': 'Resultado Esperado',
            'status': 'Estado',
        }
        widgets = {
            'test_plan': forms.HiddenInput(),
            'requirement': forms.Select(attrs={'class': 'form-select'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'TC-XXX'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título descriptivo del caso de prueba'}),
            'description': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Descripción detallada del caso de prueba', 'rows': 3}
            ),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'technique': forms.Select(attrs={'class': 'form-select', 'data-custom-technique-target': 'id_custom_technique'}),
            'custom_technique': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Especifique la técnica personalizada'}
            ),
            'preconditions': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Condiciones previas para ejecutar el caso', 'rows': 3}
            ),
            'test_data': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Usuarios, entradas y datos necesarios para ejecutar el caso', 'rows': 3}
            ),
            'steps': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': '1. Abrir el formulario de login\n2. Ingresar credenciales válidas\n3. Confirmar acceso',
                    'rows': 5,
                }
            ),
            'expected_result': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Descripción del resultado esperado', 'rows': 3}
            ),
            'status': forms.Select(attrs={'class': 'form-select'}),
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
        self.fields['requirement'].label_from_instance = lambda obj: obj.display_label
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
                        'label': requirement.display_label,
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
            'steps': 'Escribe un paso por linea numerado, por ejemplo: 1. Abrir login.',
            'priority': 'Importancia del caso para ordenar la ejecucion.',
            'technique': 'Tecnica ISTQB usada para disenar el caso, como particion de equivalencia o valores limite.',
            'status': 'Estado de preparacion o ejecucion del caso.',
        }
        for name, help_text in help_texts.items():
            self.fields[name].help_text = help_text
            self.fields[name].widget.attrs['data-help'] = help_text

    def clean_steps(self):
        steps = (self.cleaned_data.get('steps') or '').strip()
        parsed_steps = []
        expected_result_default = (self.cleaned_data.get('expected_result') or '').strip()

        for number, line in enumerate(steps.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue

            if '=>' in line:
                action, expected = (part.strip() for part in line.split('=>', 1))
                if not action or not expected:
                    raise forms.ValidationError(f'Completa la acción y el resultado esperado del paso {number}.')
                parsed_steps.append({
                    'number': len(parsed_steps) + 1,
                    'action': action,
                    'expected_result': expected,
                })
                continue

            normalized = line
            if normalized.startswith(f'{number}.'):
                normalized = normalized[number:].lstrip('. ').strip()
            elif normalized[0].isdigit() and '.' in normalized:
                _, normalized = normalized.split('.', 1)
                normalized = normalized.strip()

            if not normalized:
                raise forms.ValidationError(f'El paso {number} no puede estar vacío.')

            parsed_steps.append({
                'number': len(parsed_steps) + 1,
                'action': normalized,
                'expected_result': expected_result_default,
            })

        if not parsed_steps:
            raise forms.ValidationError('Registra al menos un paso de ejecucion.')

        self.parsed_steps = parsed_steps
        return steps

    def clean(self):
        cleaned_data = super().clean()
        test_plan = cleaned_data.get('test_plan')
        requirement = cleaned_data.get('requirement')
        if test_plan and requirement and test_plan.project_id != requirement.project_id:
            self.add_error('requirement', 'El requisito debe pertenecer al proyecto del plan seleccionado.')
        technique = cleaned_data.get('technique')
        custom = (cleaned_data.get('custom_technique') or '').strip()
        if technique == TestCase.Technique.OTHER and not custom:
            self.add_error('custom_technique', 'Especifique la técnica personalizada cuando selecciona "Otra".')
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.steps_data = getattr(self, 'parsed_steps', [])
        if commit:
            instance.save()
            self.save_m2m()
        return instance
