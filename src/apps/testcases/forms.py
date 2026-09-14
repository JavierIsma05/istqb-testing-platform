import json

from django import forms

from apps.core.codes import next_code
from apps.core.permissions import visible_projects_for
from apps.incidents.models import Incident
from apps.requirements.models import Requirement
from apps.testplans.models import TestPlan
from apps.core.lifecycle import case_changed_after_execution

from .models import TestCase


class TestCaseModalForm(forms.ModelForm):
    class Meta:
        model = TestCase
        fields = (
            'test_plan', 'requirement', 'code', 'title', 'description',
            'level', 'execution_type', 'version', 'priority', 'technique',
            'custom_technique', 'covered_risks', 'preconditions', 'test_data',
            'steps', 'expected_result', 'status',
        )
        labels = {
            'test_plan': 'Plan de Pruebas', 'requirement': 'Requisito', 'code': 'ID del Caso',
            'title': 'Título', 'description': 'Descripción', 'level': 'Nivel de prueba',
            'execution_type': 'Tipo de ejecución', 'version': 'Versión', 'priority': 'Prioridad',
            'technique': 'Técnica ISTQB', 'custom_technique': 'Técnica personalizada',
            'covered_risks': 'Riesgos cubiertos', 'preconditions': 'Precondiciones',
            'test_data': 'Datos de Prueba', 'steps': 'Pasos de Ejecución',
            'expected_result': 'Resultado Esperado', 'status': 'Estado',
        }
        widgets = {
            'test_plan': forms.HiddenInput(),
            'requirement': forms.Select(attrs={'class': 'form-select'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'TC-XXX'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título descriptivo del caso de prueba'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Descripción detallada del caso de prueba', 'rows': 3}),
            'level': forms.Select(attrs={'class': 'form-select'}),
            'execution_type': forms.Select(attrs={'class': 'form-select'}),
            'version': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1.0'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'technique': forms.Select(attrs={'class': 'form-select', 'data-custom-technique-target': 'id_custom_technique'}),
            'custom_technique': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Especifique la técnica personalizada'}),
            'covered_risks': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 4}),
            'preconditions': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Condiciones previas para ejecutar el caso', 'rows': 3}),
            'test_data': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Usuarios, entradas y datos necesarios para ejecutar el caso', 'rows': 3}),
            'steps': forms.Textarea(attrs={'class': 'form-control', 'placeholder': '1. Abrir el formulario de login\n2. Ingresar credenciales válidas\n3. Confirmar acceso', 'rows': 5}),
            'expected_result': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Descripción del resultado esperado', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        visible_projects = visible_projects_for(user) if user else None
        plan_queryset = TestPlan.objects.filter(project__in=visible_projects).order_by('project__name', 'name') if visible_projects is not None else TestPlan.objects.all().order_by('project__name', 'name')
        self.fields['test_plan'].queryset = plan_queryset
        self.fields['requirement'].required = True
        self.fields['status'].disabled = True
        self.fields['status'].help_text = 'El estado se calcula desde la revisión y ejecución del caso.'
        for field_name in ('level', 'execution_type', 'version'):
            self.fields[field_name].required = False
        test_plan_id = self.data.get('test_plan') if self.is_bound else self.instance.test_plan_id
        if not test_plan_id and not self.is_bound:
            first_plan = self.fields['test_plan'].queryset.first()
            if first_plan:
                test_plan_id = first_plan.pk
                self.fields['test_plan'].initial = first_plan.pk
        project_id = TestPlan.objects.filter(pk=test_plan_id).values_list('project_id', flat=True).first() if test_plan_id else None
        self.fields['requirement'].queryset = Requirement.objects.filter(project_id=project_id).order_by('code') if project_id else Requirement.objects.none()
        self.fields['requirement'].label_from_instance = lambda obj: obj.display_label
        self.fields['covered_risks'].queryset = Incident.objects.filter(test_plan_id=test_plan_id).order_by('code') if test_plan_id else Incident.objects.none()
        self.fields['covered_risks'].label_from_instance = lambda obj: f'{obj.code} — {obj.title}'
        queryset = TestCase.objects.filter(test_plan_id=test_plan_id) if test_plan_id else TestCase.objects.none()
        self.fields['code'].required = False
        self.fields['code'].disabled = True
        self.fields['code'].initial = self.instance.code or next_code(queryset, 'TC')
        self.fields['code'].widget.attrs.update({'placeholder': 'TC-000', 'readonly': 'readonly', 'data-default-code': 'TC-000'})
        available_plans = self.fields['test_plan'].queryset.only('id', 'project_id')
        self.fields['test_plan'].widget.attrs.update({
            'data-code-target': self.fields['code'].widget.attrs.get('id', 'id_code'),
            'data-requirement-target': self.fields['requirement'].widget.attrs.get('id', 'id_requirement'),
            'data-requirements-by-plan': json.dumps({str(plan.pk): [{'value': req.pk, 'label': req.display_label} for req in Requirement.objects.filter(project_id=plan.project_id).order_by('code')] for plan in available_plans}),
            'data-risks-by-plan': json.dumps({str(plan.pk): [{'value': risk.pk, 'label': f'{risk.code} — {risk.title}'} for risk in Incident.objects.filter(test_plan_id=plan.pk).order_by('code')] for plan in available_plans}),
            'data-next-codes': json.dumps({str(plan.pk): next_code(TestCase.objects.filter(test_plan_id=plan.pk), 'TC') for plan in available_plans}),
        })
        self.fields['requirement'].empty_label = 'Selecciona un requisito'
        help_texts = {
            'test_plan': 'Plan de pruebas donde se ejecutará o controlará este caso.',
            'requirement': 'Requisito cubierto por el caso; ayuda a medir trazabilidad.',
            'level': 'Nivel ISTQB: unitario, integración, sistema o aceptación.',
            'execution_type': 'Indica si el caso se ejecutará manualmente o mediante reglas automatizadas.',
            'version': 'Versión del diseño del caso que será revisada y ejecutada.',
            'covered_risks': 'Riesgos del plan que este caso ayuda a mitigar.',
            'test_data': 'Datos concretos que deben usarse durante la ejecución.',
            'steps': 'Escribe un paso por línea numerado; puedes añadir el resultado esperado con =>.',
            'priority': 'Importancia del caso para ordenar la ejecución.',
            'technique': 'Técnica ISTQB usada para diseñar el caso.',
            'status': 'Estado de preparación o ejecución del caso.',
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
                parsed_steps.append({'number': len(parsed_steps) + 1, 'action': action, 'expected_result': expected})
                continue
            normalized = line
            if normalized.startswith(f'{number}.'):
                normalized = normalized[number:].lstrip('. ').strip()
            elif normalized[0].isdigit() and '.' in normalized:
                _, normalized = normalized.split('.', 1)
                normalized = normalized.strip()
            if not normalized:
                raise forms.ValidationError(f'El paso {number} no puede estar vacío.')
            parsed_steps.append({'number': len(parsed_steps) + 1, 'action': normalized, 'expected_result': expected_result_default})
        if not parsed_steps:
            raise forms.ValidationError('Registra al menos un paso de ejecución.')
        self.parsed_steps = parsed_steps
        return steps

    def clean(self):
        cleaned_data = super().clean()
        test_plan = cleaned_data.get('test_plan')
        requirement = cleaned_data.get('requirement')
        covered_risks = cleaned_data.get('covered_risks')
        if test_plan and requirement and test_plan.project_id != requirement.project_id:
            self.add_error('requirement', 'El requisito debe pertenecer al proyecto del plan seleccionado.')
        if test_plan and covered_risks:
            invalid_risks = [risk.code for risk in covered_risks if risk.test_plan_id != test_plan.pk]
            if invalid_risks:
                self.add_error('covered_risks', 'Todos los riesgos seleccionados deben pertenecer al plan de pruebas actual.')
        if cleaned_data.get('technique') == TestCase.Technique.OTHER and not (cleaned_data.get('custom_technique') or '').strip():
            self.add_error('custom_technique', 'Especifique la técnica personalizada cuando selecciona "Otra".')
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.steps_data = getattr(self, 'parsed_steps', [])
        if instance.pk and case_changed_after_execution(instance, self.cleaned_data):
            instance.status = TestCase.Status.PENDING
        if commit:
            instance.save()
            self.save_m2m()
        return instance
