import json

from django import forms
from django.db.models import Q

from apps.core.codes import next_code
from apps.core.permissions import visible_projects_for
from apps.core.lifecycle import incident_transition_allowed
from apps.projects.models import Project
from apps.requirements.models import Requirement
from apps.testplans.models import TestPlan
from apps.users.models import User
from .models import Incident


class IncidentForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = (
            'project',
            'requirement',
            'test_plan',
            'code',
            'title',
            'description',
            'mitigation_strategy',
            'contingency_plan',
            'probability',
            'impact',
            'owner',
            'review_date',
        )
        labels = {
            'project': 'Proyecto',
            'requirement': 'Requisito relacionado',
            'test_plan': 'Plan relacionado',
            'code': 'Codigo',
            'title': 'Titulo del riesgo',
            'description': 'Descripcion',
            'mitigation_strategy': 'Mitigacion / respuesta',
            'contingency_plan': 'Plan de contingencia',
            'probability': 'Probabilidad',
            'impact': 'Impacto',
            'owner': 'Responsable del riesgo',
            'review_date': 'Fecha de revisión',
            'status': 'Estado',
        }
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'requirement': forms.Select(attrs={'class': 'form-select'}),
            'test_plan': forms.Select(attrs={'class': 'form-select'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. INC-001'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Riesgo de integracion con API externa'}),
            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Describe el riesgo, causa probable y efecto esperado',
                    'rows': 4,
                }
            ),
            'mitigation_strategy': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Indica como se evitara, reducira, transferira o aceptara el riesgo',
                    'rows': 4,
                }
            ),
            'contingency_plan': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Indica qué se hará si el riesgo ocurre',
                    'rows': 4,
                }
            ),
            'probability': forms.Select(attrs={'class': 'form-select'}),
            'impact': forms.Select(attrs={'class': 'form-select'}),
            'owner': forms.Select(attrs={'class': 'form-select'}),
            'review_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        visible_projects = visible_projects_for(user) if user else Project.objects.all()
        self.fields['project'].queryset = visible_projects.order_by('name')
        project_id = self.data.get('project') if self.is_bound else self.instance.project_id
        queryset = Incident.objects.filter(project_id=project_id) if project_id else Incident.objects.none()
        generated_code = self.instance.code if self.instance.pk else next_code(queryset, 'INC')
        self.instance.code = generated_code
        linked_querysets = {
            'requirement': Requirement.objects.filter(project_id=project_id) if project_id else Requirement.objects.filter(project__in=visible_projects),
            'test_plan': TestPlan.objects.filter(project_id=project_id) if project_id else TestPlan.objects.filter(project__in=visible_projects),
        }
        for field_name, linked_queryset in linked_querysets.items():
            self.fields[field_name].required = field_name == 'test_plan'
            self.fields[field_name].queryset = linked_queryset
            self.fields[field_name].empty_label = 'Selecciona un plan' if field_name == 'test_plan' else 'Sin vincular'

        member_queryset = User.objects.filter(
            Q(projects__in=visible_projects) | Q(project_created__in=visible_projects)
        ).distinct().order_by('last_name', 'first_name', 'email') if visible_projects.exists() else User.objects.none()
        self.fields['owner'].queryset = member_queryset
        self.fields['owner'].required = False
        self.fields['owner'].empty_label = 'Sin responsable asignado'
        self.fields['review_date'].required = False

        self.fields['code'].required = False
        self.fields['code'].disabled = True
        self.fields['code'].initial = generated_code
        self.fields['code'].widget.attrs.update({
            'placeholder': 'INC-000',
            'readonly': 'readonly',
            'data-default-code': 'INC-000',
        })
        self.fields['project'].widget.attrs.update({
            'data-code-target': self.fields['code'].widget.attrs.get('id', 'id_code'),
            'data-next-codes': json.dumps({
                str(project_id): next_code(Incident.objects.filter(project_id=project_id), 'INC')
                for project_id in self.fields['project'].queryset.values_list('id', flat=True)
            }),
        })
        help_texts = {
            'project': 'Proyecto donde se gestionara este riesgo.',
            'requirement': 'Requisito que podria verse afectado si el riesgo ocurre.',
            'test_plan': 'Plan de pruebas que debe considerar este riesgo para priorizar el esfuerzo.',
            'code': 'Identificador unico del riesgo, por ejemplo INC-001.',
            'title': 'Resumen breve del riesgo o bloqueo potencial.',
            'description': 'Describe causa probable, efecto esperado y contexto para darle seguimiento.',
            'mitigation_strategy': 'Describe la respuesta planificada para reducir probabilidad o impacto.',
            'contingency_plan': 'Indica la acción concreta si el riesgo se materializa.',
            'probability': 'Que tan probable es que ocurra el riesgo.',
            'impact': 'Nivel de afectacion si el riesgo ocurre.',
            'owner': 'Persona responsable de vigilar y tratar el riesgo.',
            'review_date': 'Fecha en la que debe revisarse nuevamente el riesgo.',
        }
        for name, help_text in help_texts.items():
            self.fields[name].help_text = help_text
            self.fields[name].widget.attrs['data-help'] = help_text

    def clean(self):
        cleaned_data = super().clean()
        project = cleaned_data.get('project')
        requirement = cleaned_data.get('requirement')
        test_plan = cleaned_data.get('test_plan')

        if project and requirement and requirement.project_id != project.id:
            self.add_error('requirement', 'El requisito debe pertenecer al proyecto seleccionado.')
        if project and test_plan and test_plan.project_id != project.id:
            self.add_error('test_plan', 'El plan debe pertenecer al proyecto seleccionado.')
        if project and not test_plan:
            self.add_error('test_plan', 'Todo riesgo debe estar asociado a un plan de pruebas.')
        if requirement and test_plan and requirement.project_id != test_plan.project_id:
            self.add_error('requirement', 'El requisito debe pertenecer al mismo proyecto que el plan.')
        return cleaned_data

    def clean_status(self):
        # El estado no se edita desde el formulario general: debe cambiar mediante
        # una transición explícita y validada del ciclo de vida.
        return self.instance.status
