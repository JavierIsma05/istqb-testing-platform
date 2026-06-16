from django import forms

from .models import TestPlan


class TestPlanWizardForm(forms.ModelForm):
    test_types = forms.MultipleChoiceField(
        label='Tipos de prueba',
        choices=TestPlan.TestType.choices,
        required=False,
        widget=forms.CheckboxSelectMultiple(),
    )

    class Meta:
        model = TestPlan
        fields = (
            'project',
            'name',
            'version',
            'description',
            'scope',
            'objective',
            'strategy',
            'test_types',
            'entry_criteria',
            'exit_criteria',
            'minimum_pass_percentage',
            'maximum_critical_defects',
            'minimum_coverage_percentage',
            'resources',
            'environment',
            'responsibilities',
            'estimation',
            'start_date',
            'end_date',
            'status',
        )
        labels = {
            'project': 'Proyecto',
            'name': 'Nombre del Plan',
            'version': 'Version',
            'description': 'Descripcion',
            'scope': 'Alcance',
            'objective': 'Objetivos',
            'strategy': 'Enfoque / estrategia de prueba',
            'test_types': 'Tipos de prueba',
            'entry_criteria': 'Criterios de Entrada',
            'exit_criteria': 'Criterios de Salida',
            'minimum_pass_percentage': 'Aprobacion minima (%)',
            'maximum_critical_defects': 'Defectos criticos permitidos',
            'minimum_coverage_percentage': 'Cobertura minima (%)',
            'resources': 'Recursos Necesarios',
            'environment': 'Ambiente de prueba',
            'responsibilities': 'Responsables y roles',
            'estimation': 'Estimacion de esfuerzo',
            'start_date': 'Fecha de Inicio',
            'end_date': 'Fecha de Finalizacion',
            'status': 'Estado',
        }
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Plan de Pruebas v1.0'}),
            'version': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1.0'}),
            'description': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Descripcion del plan de pruebas...', 'rows': 3}
            ),
            'scope': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Define funcionalidades incluidas y excluidas...', 'rows': 3}
            ),
            'objective': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Objetivos principales del plan...', 'rows': 3}
            ),
            'strategy': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ej. pruebas basadas en riesgo, regresion, caja negra, priorizacion por criticidad...',
                    'rows': 3,
                }
            ),
            'entry_criteria': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Condiciones para iniciar las pruebas...', 'rows': 3}
            ),
            'exit_criteria': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Condiciones para finalizar las pruebas...', 'rows': 3}
            ),
            'minimum_pass_percentage': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'maximum_critical_defects': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'minimum_coverage_percentage': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'resources': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Herramientas, datos, personas y equipos necesarios...', 'rows': 3}
            ),
            'environment': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Navegador, sistema operativo, servidor, base de datos, version...', 'rows': 3}
            ),
            'responsibilities': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Responsables de diseno, ejecucion, revision y correccion...', 'rows': 3}
            ),
            'estimation': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Horas, cantidad de casos, ventanas de ejecucion o esfuerzo esperado...', 'rows': 3}
            ),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_date'].input_formats = ['%Y-%m-%d']
        self.fields['end_date'].input_formats = ['%Y-%m-%d']
        self.fields['test_types'].initial = self.instance.test_types or [TestPlan.TestType.FUNCTIONAL]
        for field_name, default in {
            'minimum_pass_percentage': 80,
            'maximum_critical_defects': 0,
            'minimum_coverage_percentage': 90,
        }.items():
            self.fields[field_name].required = False
            self.fields[field_name].initial = getattr(self.instance, field_name, default)
        help_texts = {
            'project': 'Selecciona el proyecto al que pertenece este plan de pruebas.',
            'name': 'Usa un nombre descriptivo que permita diferenciar este plan de otros.',
            'version': 'Registra la version del plan para controlar cambios y revisiones.',
            'description': 'Explica brevemente que cubre el plan y por que se ejecutara.',
            'scope': 'Define que funcionalidades, modulos o entregables entran y cuales quedan fuera.',
            'objective': 'Describe los resultados que se esperan lograr con las pruebas.',
            'strategy': 'Describe como se seleccionaran, priorizaran y ejecutaran las pruebas.',
            'test_types': 'Selecciona los niveles o tipos incluidos en el alcance del plan.',
            'entry_criteria': 'Condiciones minimas que deben cumplirse antes de iniciar la ejecucion.',
            'exit_criteria': 'Condiciones que indican que las pruebas pueden darse por finalizadas.',
            'minimum_pass_percentage': 'Porcentaje minimo de ejecuciones aprobadas para cerrar el plan.',
            'maximum_critical_defects': 'Cantidad maxima de defectos criticos abiertos permitida.',
            'minimum_coverage_percentage': 'Porcentaje minimo de requisitos que deben tener casos asociados.',
            'resources': 'Lista personas, datos, herramientas y equipos necesarios.',
            'environment': 'Identifica ambiente, navegador, sistema, version y configuracion de prueba.',
            'responsibilities': 'Asigna responsabilidades de diseno, ejecucion, revision y seguimiento.',
            'estimation': 'Registra esfuerzo, tiempo o volumen esperado de trabajo de pruebas.',
            'start_date': 'Fecha planificada para iniciar las actividades del plan.',
            'end_date': 'Fecha planificada para terminar o cerrar el ciclo de pruebas.',
            'status': 'Marca el estado actual del plan dentro del flujo de trabajo.',
        }
        for name, help_text in help_texts.items():
            self.fields[name].help_text = help_text
            self.fields[name].widget.attrs['data-help'] = help_text

    def clean_test_types(self):
        return self.cleaned_data.get('test_types') or [TestPlan.TestType.FUNCTIONAL]

    def clean_minimum_pass_percentage(self):
        value = self.cleaned_data.get('minimum_pass_percentage')
        return 80 if value is None else value

    def clean_maximum_critical_defects(self):
        value = self.cleaned_data.get('maximum_critical_defects')
        return 0 if value is None else value

    def clean_minimum_coverage_percentage(self):
        value = self.cleaned_data.get('minimum_coverage_percentage')
        return 90 if value is None else value

    def clean(self):
        cleaned_data = super().clean()
        project = cleaned_data.get('project')
        if project and not project.requirements.exists():
            self.add_error(
                'project',
                'Primero registra al menos un requisito para este proyecto antes de crear el plan de pruebas.',
            )
        for field_name in ('minimum_pass_percentage', 'minimum_coverage_percentage'):
            value = cleaned_data.get(field_name)
            if value is not None and value > 100:
                self.add_error(field_name, 'El porcentaje debe estar entre 0 y 100.')
        return cleaned_data
