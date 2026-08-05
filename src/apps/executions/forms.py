from django import forms
from django.core.exceptions import ValidationError

from apps.core.forms import CurrentAcademicYearValidationMixin, current_year_date_attrs

from .models import AutomatedValidationRule, TestData, TestExecution

EVIDENCE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.pdf', '.txt', '.log', '.csv')
MAX_EVIDENCE_SIZE = 10 * 1024 * 1024


class ExecutionResultForm(CurrentAcademicYearValidationMixin, forms.ModelForm):
    result = forms.ChoiceField(
        label='Estado',
        choices=(
            (TestExecution.Result.PASSED, 'Aprobado'),
            (TestExecution.Result.FAILED, 'Fallido'),
            (TestExecution.Result.BLOCKED, 'Bloqueado'),
        ),
        required=False,
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = TestExecution
        fields = (
            'execution_mode',
            'execution_type',
            'related_defect',
            'planned_date',
            'result',
            'actual_result',
            'test_data',
            'environment',
            'notes',
            'evidence',
        )
        labels = {
            'execution_mode': 'Modo de ejecucion',
            'execution_type': 'Tipo de ejecucion',
            'related_defect': 'Defecto relacionado',
            'planned_date': 'Fecha de ejecución',
            'actual_result': 'Resultado obtenido',
            'test_data': 'Datos de prueba usados',
            'environment': 'Ambiente de prueba',
            'notes': 'Observaciones',
            'evidence': 'Evidencias',
        }
        widgets = {
            'execution_mode': forms.HiddenInput(),
            'execution_type': forms.HiddenInput(),
            'related_defect': forms.Select(attrs={'class': 'form-select'}),
            'planned_date': forms.DateInput(
                attrs=current_year_date_attrs({'class': 'form-control', 'type': 'date'}),
                format='%Y-%m-%d',
            ),
            'test_data': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ej. usuario, rol, entradas o datos usados durante la prueba...',
                    'rows': 3,
                }
            ),
            'environment': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ej. Chrome 125, Windows 11, ambiente local',
                }
            ),
            'notes': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Registra observaciones, bloqueos o aclaraciones adicionales...',
                    'rows': 4,
                }
            ),
            'evidence': forms.FileInput(
                attrs={
                    'accept': '.png,.jpg,.jpeg,.gif,.webp,.pdf,.txt,.log,.csv',
                    'class': 'form-control execution-file-input',
                    'data-file-input': '',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        test_case = kwargs.pop('test_case', None)
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['planned_date'].required = False
        self.fields['execution_mode'].required = False
        self.fields['execution_mode'].initial = TestExecution.ExecutionMode.MANUAL
        self.fields['execution_type'].required = False
        self.fields['execution_type'].initial = TestExecution.ExecutionType.NORMAL
        self.fields['related_defect'].required = False
        self.fields['planned_date'].input_formats = ['%Y-%m-%d']
        self.fields['notes'].required = False
        self.fields['actual_result'].required = True
        self.fields['actual_result'].error_messages['required'] = 'Selecciona el resultado obtenido: Cumple o No cumple.'
        self.fields['evidence'].required = True
        self.fields['evidence'].error_messages['required'] = 'Adjunta una captura de pantalla como evidencia de la ejecucion.'
        if user and getattr(user, 'role', None) == 'STUDENT':
            self.fields['notes'].widget.attrs['disabled'] = True
            self.fields['notes'].help_text = 'El comentario queda bloqueado para estudiantes; lo podrá escribir el docente en revisión.'
        if test_case:
            self.fields['related_defect'].queryset = test_case.test_plan.project.defects.order_by('-created_at')
        else:
            self.fields['related_defect'].queryset = self.fields['related_defect'].queryset.none()
        help_texts = {
            'execution_type': 'Usa confirmacion para verificar un defecto corregido y regresion para comprobar que no se afectaron funciones existentes.',
            'related_defect': 'Selecciona el defecto que estas confirmando o que motiva esta regresion.',
            'planned_date': 'Fecha sugerida o planificada para dar seguimiento a esta ejecucion.',
            'result': 'El estado se calcula automaticamente segun el resultado obtenido.',
            'actual_result': 'Indica si el caso de prueba cumple o no con el resultado esperado.',
            'test_data': 'Registra los datos concretos usados para que el docente pueda reproducir la ejecución.',
            'environment': 'Identifica navegador, sistema, versión o ambiente donde se ejecutó la prueba.',
            'notes': 'Registra observaciones, bloqueos o aclaraciones adicionales. Si eres estudiante, este campo queda bloqueado.',
            'evidence': 'Adjunta una captura, PDF, archivo de texto, CSV o log que respalde el resultado. Máximo 10 MB.',
        }
        for name, help_text in help_texts.items():
            self.fields[name].help_text = help_text
            self.fields[name].widget.attrs['data-help'] = help_text

    def clean(self):
        cleaned_data = super().clean()
        result = cleaned_data.get('result')
        execution_type = cleaned_data.get('execution_type')
        related_defect = cleaned_data.get('related_defect')
        actual_result = (cleaned_data.get('actual_result') or '').strip()

        if execution_type == TestExecution.ExecutionType.CONFIRMATION and not related_defect:
            self.add_error(
                'related_defect',
                'Selecciona el defecto que se confirma con esta ejecucion.',
            )

        # Deriva el estado a partir del resultado obtenido (solo para los valores del formulario).
        if actual_result in {'Cumple', 'No cumple'}:
            cleaned_data['result'] = (
                TestExecution.Result.PASSED
                if actual_result == 'Cumple'
                else TestExecution.Result.FAILED
            )

        if result in {
            TestExecution.Result.PASSED,
            TestExecution.Result.FAILED,
            TestExecution.Result.BLOCKED,
        } and not actual_result:
            self.add_error(
                'actual_result',
                'Registra el resultado obtenido para justificar si el caso aprobo o fallo.',
            )

        return cleaned_data

    def clean_evidence(self):
        evidence = self.cleaned_data.get('evidence')
        if not evidence:
            return evidence

        filename = evidence.name.lower()
        if not filename.endswith(EVIDENCE_EXTENSIONS):
            raise forms.ValidationError('La evidencia debe ser una imagen, PDF, TXT, LOG o CSV.')
        if evidence.size > MAX_EVIDENCE_SIZE:
            raise forms.ValidationError('La evidencia no debe superar 10 MB.')
        return evidence


class ExecutionReviewForm(forms.ModelForm):
    class Meta:
        model = TestExecution
        fields = ('review_status', 'review_notes')
        labels = {
            'review_status': 'Revisión docente',
            'review_notes': 'Comentario del docente',
        }
        widgets = {
            'review_status': forms.Select(attrs={'class': 'form-select'}),
            'review_notes': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Indica si la evidencia es suficiente o que debe corregirse...',
                    'rows': 3,
                }
            ),
        }


class TestDataForm(forms.ModelForm):
    class Meta:
        model = TestData
        fields = ('key', 'value')
        labels = {
            'key': 'Nombre de variable',
            'value': 'Valor',
        }
        widgets = {
            'key': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej. usuario, clave, url_base'}),
            'value': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej. javier.aguilar@unl.edu.ec, Test1234, http://localhost:8000'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['key'].help_text = 'Nombre de la variable para usar en pasos como {{nombre}}'
        self.fields['value'].help_text = 'Valor que se reemplazará al ejecutar'


class AutomatedStepForm(forms.ModelForm):
    name = forms.CharField(
        label='Nombre del paso',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional: se genera solo'}),
    )
    template = forms.ChoiceField(
        label='Usar plantilla',
        required=False,
        choices=[
            ('', '-- Seleccionar plantilla --'),
            ('login', 'Login estándar'),
            ('search', 'Búsqueda simple'),
            ('form_submit', 'Envío de formulario'),
        ],
        widget=forms.Select(attrs={'class': 'form-select', 'data-template-select': ''}),
    )

    class Meta:
        model = AutomatedValidationRule
        fields = (
            'name',
            'step_number',
            'action_type',
            'target_url',
            'selector_value',
            'input_value',
            'expected_value',
            'comparison_type',
            'timeout_seconds',
            'is_critical',
        )
        labels = {
            'step_number': 'Paso',
            'action_type': 'Acción',
            'target_url': 'URL a abrir',
            'selector_value': 'Elemento',
            'input_value': 'Dato',
            'expected_value': 'Resultado esperado',
            'comparison_type': 'Tipo de comparación',
            'timeout_seconds': 'Duración en segundos',
            'is_critical': 'Paso crítico',
        }
        widgets = {
            'step_number': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'value': 1}),
            'action_type': forms.Select(attrs={'class': 'form-select'}),
            'target_url': forms.URLInput(
                attrs={'class': 'form-control', 'placeholder': 'http://localhost:8000/'}
            ),
            'selector_value': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': '#usuario, input[name="password"], .btn-login'}
            ),
            'input_value': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Valor a escribir o seleccionar (acepta {{variable}})' }
            ),
            'expected_value': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Valor, texto o URL esperada'}
            ),
            'comparison_type': forms.Select(attrs={'class': 'form-select'}),
            'timeout_seconds': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 60, 'value': 10}),
            'is_critical': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.test_case = kwargs.pop('test_case', None)
        super().__init__(*args, **kwargs)
        help_texts = {
            'name': 'Opcional. Si lo dejas vacio se genera automaticamente desde la accion.',
            'step_number': 'Orden del paso dentro del caso de prueba.',
            'action_type': 'Accion segura que ejecutara el navegador. No se permite codigo libre.',
            'target_url': 'Direccion que abrira la automatizacion. Solo URLs autorizadas como localhost.',
            'selector_value': 'Elemento de la pagina usando CSS. Ejemplos: #usuario, .btn-login.',
            'input_value': 'Dato que se escribira o seleccionara en el elemento. Acepta variables como {{usuario}}.',
            'expected_value': 'Resultado esperado para la verificacion.',
            'comparison_type': 'Como comparar el resultado: Exacto (igualdad estricta), Contiene (substring), Expresion regular (regex).',
            'timeout_seconds': 'Para la accion Esperar es la duracion; para el resto es el tiempo maximo de espera.',
            'is_critical': 'Si el paso falla, la ejecucion se detiene y los siguientes quedan NO EJECUTADOS.',
        }
        for name, help_text in help_texts.items():
            self.fields[name].help_text = help_text
            self.fields[name].widget.attrs['data-help'] = help_text
        self.fields['timeout_seconds'].required = False
        self.fields['target_url'].required = False
        self.fields['target_url'].initial = ''
        self.fields['comparison_type'].required = False
        self.fields['comparison_type'].initial = AutomatedValidationRule.ComparisonType.EXACT
        
        # Add data attributes for dynamic field visibility
        self.fields['target_url'].widget.attrs['data-action'] = 'OPEN_URL'
        self.fields['selector_value'].widget.attrs['data-action'] = 'CLICK FILL_TEXT VERIFY'
        self.fields['input_value'].widget.attrs['data-action'] = 'FILL_TEXT WAIT'
        self.fields['expected_value'].widget.attrs['data-action'] = 'VERIFY'
        self.fields['comparison_type'].widget.attrs['data-action'] = 'VERIFY'
        self.fields['timeout_seconds'].widget.attrs['data-action'] = 'WAIT'

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action_type')
        if not action:
            self.add_error('action_type', 'Selecciona una accion para el paso.')
            return cleaned_data

        step_number = cleaned_data.get('step_number')
        if step_number and not cleaned_data.get('name'):
            label = dict(AutomatedValidationRule.ActionType.choices).get(action, '')
            cleaned_data['name'] = f'Paso {step_number}: {label}'

        # OPEN_URL: only target_url required
        if action == AutomatedValidationRule.ActionType.OPEN_URL:
            url = cleaned_data.get('target_url')
            if not url:
                self.add_error('target_url', 'Indica la URL que debe abrirse.')
            else:
                from .services.automated_runner import validate_automation_url
                try:
                    validate_automation_url(url)
                except ValidationError as exc:
                    self.add_error('target_url', exc)

        # CLICK: only selector_value required
        elif action == AutomatedValidationRule.ActionType.CLICK:
            if not (cleaned_data.get('selector_value') or '').strip():
                self.add_error('selector_value', 'Esta accion requiere un elemento (selector CSS).')

        # FILL_TEXT: selector_value and input_value required
        elif action == AutomatedValidationRule.ActionType.FILL_TEXT:
            if not (cleaned_data.get('selector_value') or '').strip():
                self.add_error('selector_value', 'Esta accion requiere un elemento (selector CSS).')
            if not (cleaned_data.get('input_value') or '').strip():
                self.add_error('input_value', 'Indica el dato que debe ingresarse.')

        # VERIFY: selector_value, expected_value, and comparison_type required
        elif action == AutomatedValidationRule.ActionType.VERIFY:
            if not (cleaned_data.get('selector_value') or '').strip():
                self.add_error('selector_value', 'Esta accion requiere un elemento (selector CSS) o "URL actual".')
            if not (cleaned_data.get('expected_value') or '').strip():
                self.add_error('expected_value', 'Indica el resultado esperado de la verificacion.')
            if not (cleaned_data.get('comparison_type') or '').strip():
                cleaned_data['comparison_type'] = AutomatedValidationRule.ComparisonType.EXACT

        # WAIT: timeout_seconds (duration) or selector_value (wait for element)
        elif action == AutomatedValidationRule.ActionType.WAIT:
            duration = cleaned_data.get('timeout_seconds') or 10
            selector = cleaned_data.get('selector_value')
            if not selector and duration < 1:
                self.add_error('timeout_seconds', 'Indica segundos de espera o un selector a esperar.')
            cleaned_data['timeout_seconds'] = min(duration, 60)

        return cleaned_data
