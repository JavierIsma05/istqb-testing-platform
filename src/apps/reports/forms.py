from django import forms

from .models import Report


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ('project', 'title', 'report_type')
        labels = {
            'project': 'Proyecto',
            'title': 'Título',
            'report_type': 'Tipo de reporte',
        }
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Informe de Cobertura'}),
            'report_type': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        help_texts = {
            'project': 'Proyecto del que se generará la información del reporte.',
            'title': 'Nombre visible del reporte para identificarlo en el historial.',
            'report_type': 'Tipo de análisis o resumen que necesitas generar.',
        }
        for name, help_text in help_texts.items():
            self.fields[name].help_text = help_text
            self.fields[name].widget.attrs['data-help'] = help_text
