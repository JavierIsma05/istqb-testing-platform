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
