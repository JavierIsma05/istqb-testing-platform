from django import forms

from .models import TestPlan


class TestPlanWizardForm(forms.ModelForm):
    class Meta:
        model = TestPlan
        fields = (
            'project',
            'name',
            'version',
            'description',
            'scope',
            'objective',
            'entry_criteria',
            'exit_criteria',
            'resources',
            'start_date',
            'end_date',
            'status',
        )
        labels = {
            'project': 'Proyecto',
            'name': 'Nombre del Plan',
            'version': 'Versión',
            'description': 'Descripción',
            'scope': 'Alcance',
            'objective': 'Objetivos',
            'entry_criteria': 'Criterios de Entrada',
            'exit_criteria': 'Criterios de Salida',
            'resources': 'Recursos Necesarios',
            'start_date': 'Fecha de Inicio',
            'end_date': 'Fecha de Finalización',
            'status': 'Estado',
        }
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Plan de Pruebas v1.0'}),
            'version': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1.0'}),
            'description': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Descripción del plan de pruebas...', 'rows': 3}
            ),
            'scope': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Define el alcance de las pruebas...', 'rows': 3}
            ),
            'objective': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Objetivos principales del plan...', 'rows': 3}
            ),
            'entry_criteria': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Condiciones para iniciar las pruebas...', 'rows': 3}
            ),
            'exit_criteria': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Condiciones para finalizar las pruebas...', 'rows': 3}
            ),
            'resources': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Hardware, software, personal...', 'rows': 3}
            ),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_date'].input_formats = ['%Y-%m-%d']
        self.fields['end_date'].input_formats = ['%Y-%m-%d']
        help_texts = {
            'project': 'Selecciona el proyecto al que pertenece este plan de pruebas.',
            'name': 'Usa un nombre descriptivo que permita diferenciar este plan de otros.',
            'version': 'Registra la version del plan para controlar cambios y revisiones.',
            'description': 'Explica brevemente que cubre el plan y por que se ejecutara.',
            'scope': 'Define que funcionalidades, modulos o entregables entran y cuales quedan fuera.',
            'objective': 'Describe los resultados que se esperan lograr con las pruebas.',
            'entry_criteria': 'Condiciones minimas que deben cumplirse antes de iniciar la ejecucion.',
            'exit_criteria': 'Condiciones que indican que las pruebas pueden darse por finalizadas.',
            'resources': 'Lista personas, ambientes, datos, herramientas y equipos necesarios.',
            'start_date': 'Fecha planificada para iniciar las actividades del plan.',
            'end_date': 'Fecha planificada para terminar o cerrar el ciclo de pruebas.',
            'status': 'Marca el estado actual del plan dentro del flujo de trabajo.',
        }
        for name, help_text in help_texts.items():
            self.fields[name].help_text = help_text
            self.fields[name].widget.attrs['data-help'] = help_text
