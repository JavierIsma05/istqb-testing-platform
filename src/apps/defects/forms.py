import json

from django import forms

from apps.core.codes import next_code
from apps.projects.models import Project

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
            'steps_to_reproduce',
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
            'steps_to_reproduce': 'Pasos para reproducir',
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
            'steps_to_reproduce': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': '1. Abrir...\n2. Ejecutar...\n3. Observar...',
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
        self.fields['execution'].required = True
        self.fields['assigned_to'].required = False
        project_id = self.data.get('project') if self.is_bound else self.instance.project_id
        execution_queryset = self.fields['execution'].queryset.filter(result='FAILED')
        if project_id:
            execution_queryset = execution_queryset.filter(test_case__test_plan__project_id=project_id)
        self.fields['execution'].queryset = execution_queryset.select_related('test_case')
        self.fields['execution'].empty_label = 'Selecciona una ejecucion fallida'
        queryset = Defect.objects.filter(project_id=project_id) if project_id else Defect.objects.none()
        self.fields['code'].required = False
        self.fields['code'].disabled = True
        self.fields['code'].initial = self.instance.code or next_code(queryset, 'DEF')
        self.fields['code'].widget.attrs.update({
            'placeholder': 'DEF-000',
            'readonly': 'readonly',
            'data-default-code': 'DEF-000',
        })
        self.fields['project'].widget.attrs.update({
            'data-code-target': self.fields['code'].widget.attrs.get('id', 'id_code'),
            'data-next-codes': json.dumps({
                str(project_id): next_code(Defect.objects.filter(project_id=project_id), 'DEF')
                for project_id in Project.objects.values_list('id', flat=True)
            }),
        })
        help_texts = {
            'project': 'Proyecto donde se encontro el defecto.',
            'execution': 'Ejecucion fallida que origino el defecto.',
            'code': 'Identificador unico del defecto, por ejemplo DEF-001.',
            'title': 'Resumen corto del problema observado.',
            'description': 'Incluye pasos para reproducir, resultado obtenido y resultado esperado.',
            'steps_to_reproduce': 'Secuencia concreta para reproducir el defecto.',
            'severity': 'Impacto tecnico o funcional del defecto en el sistema.',
            'priority': 'Urgencia con la que deberia atenderse el defecto.',
            'status': 'Estado actual del seguimiento del defecto.',
            'assigned_to': 'Responsable sugerido para analizar o corregir el defecto.',
        }
        for name, help_text in help_texts.items():
            self.fields[name].help_text = help_text
            self.fields[name].widget.attrs['data-help'] = help_text

    def clean(self):
        cleaned_data = super().clean()
        project = cleaned_data.get('project')
        execution = cleaned_data.get('execution')
        if not execution:
            self.add_error('execution', 'Todo defecto debe originarse en una ejecucion fallida.')
        elif execution.result != execution.Result.FAILED:
            self.add_error('execution', 'Solo una ejecucion fallida puede originar un defecto.')
        elif project and execution.test_case.test_plan.project_id != project.id:
            self.add_error('execution', 'La ejecucion debe pertenecer al proyecto seleccionado.')
        return cleaned_data
