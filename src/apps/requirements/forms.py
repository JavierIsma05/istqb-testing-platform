from django import forms

from .models import Requirement


class RequirementForm(forms.ModelForm):
    class Meta:
        model = Requirement
        fields = (
            'project',
            'code',
            'title',
            'description',
            'requirement_type',
            'priority',
            'status',
        )
        labels = {
            'project': 'Proyecto',
            'code': 'Código',
            'title': 'Nombre del requisito',
            'description': 'Descripción',
            'requirement_type': 'Tipo',
            'priority': 'Prioridad',
            'status': 'Estado',
        }
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. REQ-001'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Login de usuarios'}),
            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Describe el comportamiento, regla o restricción del requisito',
                    'rows': 5,
                }
            ),
            'requirement_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
