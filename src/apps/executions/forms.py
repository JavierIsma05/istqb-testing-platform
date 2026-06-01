from django import forms

from .models import TestExecution


class ExecutionResultForm(forms.ModelForm):
    result = forms.ChoiceField(
        label='Resultado',
        choices=(
            (TestExecution.Result.PASSED, 'Passed'),
            (TestExecution.Result.FAILED, 'Failed'),
            (TestExecution.Result.BLOCKED, 'Blocked'),
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
            'evidence': forms.FileInput(attrs={'class': 'form-control execution-file-input'}),
        }
