from django import forms

from apps.core.codes import next_code
from apps.core.permissions import visible_projects_for
from apps.executions.models import TestExecution
from apps.projects.models import Project
from apps.testcases.models import TestCase

from .models import Defect


class DefectForm(forms.ModelForm):
    class Meta:
        model = Defect
        fields = (
            'test_case',
            'execution',
            'title',
            'description',
            'assigned_to',
            'resolution',
            'verification_execution',
            'severity',
        )
        labels = {
            'test_case': 'Caso de prueba',
            'execution': 'Ejecución relacionada (opcional)',
            'title': 'Título del defecto',
            'description': 'Descripción',
            'assigned_to': 'Responsable',
            'resolution': 'Resolución',
            'verification_execution': 'Ejecución de confirmación',
            'severity': 'Severidad',
        }
        widgets = {
            'test_case': forms.Select(attrs={'class': 'form-select'}),
            'execution': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Error al cargar imágenes grandes'}),
            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Describe el defecto, el comportamiento esperado y lo observado',
                    'rows': 4,
                }
            ),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'resolution': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'verification_execution': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        visible_projects = visible_projects_for(user) if user else Project.objects.all()

        test_case_queryset = TestCase.objects.filter(test_plan__project__in=visible_projects)
        self.fields['test_case'].required = True
        self.fields['test_case'].queryset = test_case_queryset.select_related('test_plan').order_by('code')
        self.fields['test_case'].empty_label = 'Selecciona un caso de prueba'

        execution_queryset = TestExecution.objects.filter(
            result=TestExecution.Result.FAILED,
            test_case__test_plan__project__in=visible_projects,
        )
        self.fields['execution'].required = False
        self.fields['execution'].queryset = execution_queryset.select_related('test_case', 'test_case__test_plan')
        self.fields['execution'].empty_label = 'Sin ejecución relacionada'
        self.fields['verification_execution'].queryset = TestExecution.objects.filter(
            test_case__test_plan__project__in=visible_projects,
            execution_type=TestExecution.ExecutionType.CONFIRMATION,
        ).select_related('test_case').order_by('-executed_at')
        self.fields['verification_execution'].required = False
        self.fields['verification_execution'].empty_label = 'Sin confirmación todavía'
        from apps.users.models import User
        self.fields['assigned_to'].queryset = User.objects.filter(projects__id__in=visible_projects.values('id')).distinct() if visible_projects.exists() else User.objects.none()
        self.fields['assigned_to'].required = False

        help_texts = {
            'test_case': 'Caso de prueba que reveló el defecto.',
            'execution': 'Opcional: ejecución fallida que originó el defecto, como evidencia.',
            'title': 'Resumen corto del problema observado.',
            'description': 'Incluye el comportamiento esperado y el resultado obtenido.',
            'severity': 'Impacto técnico o funcional del defecto en el sistema.',
        }
        for name, help_text in help_texts.items():
            self.fields[name].help_text = help_text
            self.fields[name].widget.attrs['data-help'] = help_text

    def clean(self):
        cleaned_data = super().clean()
        test_case = cleaned_data.get('test_case')
        execution = cleaned_data.get('execution')
        if not test_case:
            self.add_error('test_case', 'Todo defecto debe asociarse a un caso de prueba.')
        if execution and test_case and execution.test_case_id != test_case.pk:
            self.add_error('execution', 'La ejecución debe corresponder al caso de prueba seleccionado.')
        verification = cleaned_data.get('verification_execution')
        if verification and test_case and verification.test_case_id != test_case.pk:
            self.add_error('verification_execution', 'La confirmación debe corresponder al caso de prueba del defecto.')
        if verification and verification.result != TestExecution.Result.PASSED:
            self.add_error('verification_execution', 'La ejecución de confirmación debe estar aprobada.')
        return cleaned_data

    def _post_clean(self):
        # `project` is intentionally not exposed as a form field; derive it
        # from the selected test case before ModelForm runs model validation.
        test_case = self.cleaned_data.get('test_case')
        if test_case:
            self.instance.project_id = test_case.test_plan.project_id
        super()._post_clean()

    def save(self, commit=True):
        defect = super().save(commit=False)
        if defect.project_id is None:
            defect.project_id = defect.test_case.test_plan.project_id
        if defect.code in (None, '', 'DEF-000'):
            queryset = Defect.objects.filter(project_id=defect.project_id)
            defect.code = next_code(queryset, 'DEF')
        if defect.status in (None, ''):
            defect.status = Defect.Status.OPEN
        if commit:
            defect.save()
        return defect
