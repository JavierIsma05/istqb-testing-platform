import json

from django import forms

from apps.core.codes import next_code
from apps.projects.models import Project

from .models import Incident


class IncidentForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = ('project', 'code', 'title', 'description', 'probability', 'impact', 'status')
        labels = {
            'project': 'Proyecto',
            'code': 'Código',
            'title': 'Título de la incidencia',
            'description': 'Descripción',
            'probability': 'Probabilidad',
            'impact': 'Impacto',
            'status': 'Estado',
        }
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. INC-001'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Riesgo de integración con API externa'}),
            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Describe el riesgo, incidencia, causa probable y efecto esperado',
                    'rows': 4,
                }
            ),
            'probability': forms.Select(attrs={'class': 'form-select'}),
            'impact': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        project_id = self.data.get('project') if self.is_bound else self.instance.project_id
        queryset = Incident.objects.filter(project_id=project_id) if project_id else Incident.objects.none()
        self.fields['code'].required = False
        self.fields['code'].disabled = True
        self.fields['code'].initial = self.instance.code or next_code(queryset, 'INC')
        self.fields['code'].widget.attrs.update({
            'placeholder': 'INC-000',
            'readonly': 'readonly',
            'data-default-code': 'INC-000',
        })
        self.fields['project'].widget.attrs.update({
            'data-code-target': self.fields['code'].widget.attrs.get('id', 'id_code'),
            'data-next-codes': json.dumps({
                str(project_id): next_code(Incident.objects.filter(project_id=project_id), 'INC')
                for project_id in Project.objects.values_list('id', flat=True)
            }),
        })
        help_texts = {
            'project': 'Proyecto afectado por la incidencia o riesgo registrado.',
            'code': 'Identificador unico de la incidencia, por ejemplo INC-001.',
            'title': 'Resumen breve de la incidencia, riesgo o bloqueo.',
            'description': 'Describe causa probable, efecto esperado y contexto para darle seguimiento.',
            'probability': 'Que tan probable es que ocurra o se repita esta incidencia.',
            'impact': 'Nivel de afectacion si la incidencia ocurre.',
            'status': 'Estado actual de gestion de la incidencia.',
        }
        for name, help_text in help_texts.items():
            self.fields[name].help_text = help_text
            self.fields[name].widget.attrs['data-help'] = help_text
