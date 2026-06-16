from django import forms
from django.core.exceptions import ValidationError

from .models import AutomatedValidationRule, TestExecution


class ExecutionResultForm(forms.ModelForm):
    result = forms.ChoiceField(
        label='Resultado',
        choices=(
            (TestExecution.Result.PASSED, 'Aprobado'),
            (TestExecution.Result.FAILED, 'Fallido'),
            (TestExecution.Result.BLOCKED, 'Bloqueado'),
        ),
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
            'planned_date': 'Fecha planificada',
            'actual_result': 'Resultado obtenido',
            'test_data': 'Datos de prueba usados',
            'environment': 'Ambiente de prueba',
            'notes': 'Observaciones',
            'evidence': 'Evidencias',
        }
        widgets = {
            'execution_mode': forms.HiddenInput(),
            'execution_type': forms.Select(attrs={'class': 'form-select'}),
            'related_defect': forms.Select(attrs={'class': 'form-select'}),
            'planned_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'actual_result': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Describe lo que realmente ocurrio al ejecutar el caso...',
                    'rows': 3,
                }
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
                    'accept': 'image/*',
                    'class': 'form-control execution-file-input',
                    'data-file-input': '',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        test_case = kwargs.pop('test_case', None)
        super().__init__(*args, **kwargs)
        self.fields['planned_date'].required = False
        self.fields['execution_mode'].required = False
        self.fields['execution_mode'].initial = TestExecution.ExecutionMode.MANUAL
        self.fields['related_defect'].required = False
        self.fields['planned_date'].input_formats = ['%Y-%m-%d']
        if test_case:
            self.fields['related_defect'].queryset = test_case.test_plan.project.defects.order_by('-created_at')
        else:
            self.fields['related_defect'].queryset = self.fields['related_defect'].queryset.none()
        help_texts = {
            'execution_type': 'Usa confirmacion para verificar un defecto corregido y regresion para comprobar que no se afectaron funciones existentes.',
            'related_defect': 'Selecciona el defecto que estas confirmando o que motiva esta regresion.',
            'planned_date': 'Fecha sugerida o planificada para dar seguimiento a esta ejecucion.',
            'result': 'Selecciona el resultado observado durante la ejecucion del caso.',
            'actual_result': 'Compara este resultado con el resultado esperado del caso de prueba.',
            'test_data': 'Registra los datos concretos usados para que el docente pueda reproducir la ejecucion.',
            'environment': 'Identifica navegador, sistema, version o ambiente donde se ejecuto la prueba.',
            'notes': 'Registra bloqueos o diferencias encontradas durante la ejecucion.',
            'evidence': 'Adjunta una captura que respalde el resultado de la ejecucion.',
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


class AutomatedValidationRuleForm(forms.ModelForm):
    BROWSER_CHOICES = (('chromium', 'Chromium'),)
    browser = forms.ChoiceField(
        label='Navegador',
        choices=BROWSER_CHOICES,
        initial='chromium',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = AutomatedValidationRule
        fields = (
            'name',
            'step_number',
            'validation_type',
            'target_url',
            'selector_type',
            'selector_value',
            'secondary_selector_value',
            'input_value',
            'expected_value',
            'expected_text',
            'min_length',
            'max_length',
            'expected_url',
            'expected_http_status',
            'timeout_seconds',
            'browser',
            'capture_evidence',
            'is_active',
        )
        labels = {
            'name': 'Nombre de la regla',
            'step_number': 'Numero de paso',
            'validation_type': 'Tipo de validacion',
            'target_url': 'URL objetivo',
            'selector_type': 'Tipo de selector',
            'selector_value': 'Selector principal',
            'secondary_selector_value': 'Selector secundario',
            'input_value': 'Dato de prueba',
            'expected_value': 'Valor esperado',
            'expected_text': 'Texto esperado',
            'min_length': 'Longitud minima',
            'max_length': 'Longitud maxima',
            'expected_url': 'URL esperada',
            'expected_http_status': 'Estado HTTP esperado',
            'timeout_seconds': 'Timeout en segundos',
            'browser': 'Navegador',
            'capture_evidence': 'Generar evidencia automatica',
            'is_active': 'Regla activa',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'step_number': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'validation_type': forms.Select(attrs={'class': 'form-select'}),
            'target_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'http://localhost:8000/'}),
            'selector_type': forms.Select(attrs={'class': 'form-select'}),
            'selector_value': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '#password'}),
            'secondary_selector_value': forms.TextInput(attrs={'class': 'form-control'}),
            'input_value': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'expected_value': forms.TextInput(attrs={'class': 'form-control'}),
            'expected_text': forms.TextInput(attrs={'class': 'form-control'}),
            'min_length': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'max_length': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'expected_url': forms.URLInput(attrs={'class': 'form-control'}),
            'expected_http_status': forms.NumberInput(attrs={'class': 'form-control', 'min': 100, 'max': 599}),
            'timeout_seconds': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 60}),
            'capture_evidence': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.test_case = kwargs.pop('test_case', None)
        super().__init__(*args, **kwargs)
        help_texts = {
            'name': 'Nombre corto para reconocer la regla en el historial. Ejemplo: Titulo de login visible.',
            'step_number': 'Numero del paso manual que esta regla valida. Debe existir en el caso de prueba.',
            'validation_type': 'Define que comprobara la regla: texto visible, estado HTTP, campo obligatorio, redireccion, etc.',
            'target_url': 'Pagina que abrira la automatizacion. Solo se permiten URLs autorizadas como localhost o 127.0.0.1.',
            'selector_type': 'Forma de ubicar un elemento en la pagina. Para la mayoria de casos usa CSS.',
            'selector_value': 'Elemento principal que se validara o rellenara. Ejemplos CSS: #email, input[name="password"], .btn-login.',
            'secondary_selector_value': 'Boton o elemento que dispara el envio del formulario. Ejemplo: button[type="submit"].',
            'input_value': 'Dato que la prueba escribira en el campo principal. Se usa en email, longitud minima/maxima o envio bloqueado.',
            'expected_value': 'Valor esperado generico. Usalo solo si el tipo de validacion lo necesita.',
            'expected_text': 'Texto que debe aparecer visible en la pagina. Ejemplo: Iniciar Sesion.',
            'min_length': 'Cantidad minima esperada cuando se valida longitud minima.',
            'max_length': 'Cantidad maxima permitida cuando se valida longitud maxima.',
            'expected_url': 'URL final esperada despues de hacer clic en el selector principal.',
            'expected_http_status': 'Codigo HTTP esperado para la URL objetivo. Ejemplo: 200, 302 o 404.',
            'timeout_seconds': 'Tiempo maximo de espera antes de marcar error tecnico. Usa 10 segundos salvo que la pagina sea lenta.',
            'browser': 'Navegador usado para reglas visuales. Actualmente la plataforma ejecuta Chromium.',
            'capture_evidence': 'Guarda captura automatica cuando la regla se ejecuta en navegador.',
            'is_active': 'Si esta marcado, la regla se incluye al ejecutar validaciones automatizadas.',
        }
        placeholders = {
            'name': 'Ej. Titulo de login visible',
            'secondary_selector_value': 'Ej. button[type="submit"]',
            'input_value': 'Ej. correo-invalido, texto demasiado largo o valor de prueba',
            'expected_value': 'Ej. valor exacto esperado',
            'expected_text': 'Ej. Iniciar Sesion',
            'expected_url': 'Ej. http://localhost:8000/dashboard/',
            'expected_http_status': 'Ej. 200',
        }
        for name, help_text in help_texts.items():
            self.fields[name].help_text = help_text
            self.fields[name].widget.attrs['data-help'] = help_text
            if name in placeholders:
                self.fields[name].widget.attrs.setdefault('placeholder', placeholders[name])

    def clean(self):
        cleaned_data = super().clean()
        validation_type = cleaned_data.get('validation_type')
        step_number = cleaned_data.get('step_number')
        selector_value = (cleaned_data.get('selector_value') or '').strip()
        secondary_selector = (cleaned_data.get('secondary_selector_value') or '').strip()

        if self.test_case and step_number and step_number > len(self.test_case.steps_data or []):
            fallback_steps = [line for line in (self.test_case.steps or '').splitlines() if line.strip()]
            if step_number > len(fallback_steps):
                self.add_error('step_number', 'El paso seleccionado no existe en el caso de prueba.')

        if validation_type == AutomatedValidationRule.ValidationType.HTTP_STATUS:
            if not cleaned_data.get('expected_http_status'):
                self.add_error('expected_http_status', 'Indica el codigo HTTP esperado.')
        elif validation_type != AutomatedValidationRule.ValidationType.TEXT_VISIBLE and not selector_value:
            self.add_error('selector_value', 'Esta validacion requiere un selector principal.')

        submit_validations = {
            AutomatedValidationRule.ValidationType.FIELD_REQUIRED,
            AutomatedValidationRule.ValidationType.EMAIL_FORMAT,
            AutomatedValidationRule.ValidationType.MAX_LENGTH,
            AutomatedValidationRule.ValidationType.MIN_LENGTH,
            AutomatedValidationRule.ValidationType.FORM_SUBMISSION_BLOCKED,
        }
        if validation_type in submit_validations and not secondary_selector:
            self.add_error('secondary_selector_value', 'Indica el selector CSS del boton de envio.')
        if validation_type == AutomatedValidationRule.ValidationType.EMAIL_FORMAT and not cleaned_data.get('input_value'):
            self.add_error('input_value', 'Indica el correo invalido que se probara.')
        if validation_type == AutomatedValidationRule.ValidationType.MAX_LENGTH:
            if cleaned_data.get('max_length') is None:
                self.add_error('max_length', 'Indica la longitud maxima permitida.')
            if not cleaned_data.get('input_value'):
                self.add_error('input_value', 'Indica un valor que supere la longitud maxima.')
        if validation_type == AutomatedValidationRule.ValidationType.MIN_LENGTH:
            if cleaned_data.get('min_length') is None:
                self.add_error('min_length', 'Indica la longitud minima permitida.')
            if not cleaned_data.get('input_value'):
                self.add_error('input_value', 'Indica un valor menor que la longitud minima.')
        if validation_type == AutomatedValidationRule.ValidationType.TEXT_VISIBLE and not cleaned_data.get('expected_text'):
            self.add_error('expected_text', 'Indica el texto que debe aparecer.')
        if validation_type == AutomatedValidationRule.ValidationType.REDIRECT_URL and not cleaned_data.get('expected_url'):
            self.add_error('expected_url', 'Indica la URL de destino esperada.')

        timeout = cleaned_data.get('timeout_seconds')
        if timeout and timeout > 60:
            self.add_error('timeout_seconds', 'El timeout maximo permitido es 60 segundos.')

        target_url = cleaned_data.get('target_url')
        if target_url:
            from .services.automated_runner import validate_automation_url

            try:
                validate_automation_url(target_url)
            except ValidationError as exc:
                self.add_error('target_url', exc)
        return cleaned_data


class ExecutionReviewForm(forms.ModelForm):
    class Meta:
        model = TestExecution
        fields = ('review_status', 'review_notes')
        labels = {
            'review_status': 'Revision docente',
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
