from django import forms

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
