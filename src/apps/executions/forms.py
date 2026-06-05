from django import forms

from .models import TestExecution


class ExecutionResultForm(forms.ModelForm):
    result = forms.ChoiceField(
        label='Resultado',
        choices=(
            (TestExecution.Result.PASSED, 'Aprobado'),
            (TestExecution.Result.FAILED, 'Fallido'),
            (TestExecution.Result.BLOCKED, 'Bloqueado'),
        ),
        widget=forms.RadioSelect(attrs={'class': 'execution-result-input'}),
    )

    class Meta:
        model = TestExecution
        fields = ('result', 'notes', 'evidence')
        labels = {
            'notes': 'Observaciones',
            'evidence': 'Evidencias',
        }
        widgets = {
            'notes': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Describe el resultado de la ejecución...',
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
        super().__init__(*args, **kwargs)
        help_texts = {
            'result': 'Selecciona el resultado observado durante la ejecucion del caso.',
            'notes': 'Registra observaciones, datos usados, bloqueos o diferencias encontradas.',
            'evidence': 'Adjunta una captura que respalde el resultado de la ejecucion.',
        }
        for name, help_text in help_texts.items():
            self.fields[name].help_text = help_text
            self.fields[name].widget.attrs['data-help'] = help_text
