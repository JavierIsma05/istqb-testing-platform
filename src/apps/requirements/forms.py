import json

from django import forms

from apps.core.codes import next_code
from apps.core.permissions import visible_projects_for
from apps.projects.models import Project

from .models import Requirement


class RequirementForm(forms.ModelForm):
    class Meta:
        model = Requirement
        fields = (
            'project',
            'code',
            'title',
            'description',
            'acceptance_criteria',
            'requirement_type',
            'priority',
            'status',
        )
        labels = {
            'project': 'Proyecto',
            'code': 'Código',
            'title': 'Nombre del requisito',
            'description': 'Descripción',
            'acceptance_criteria': 'Criterios de aceptación',
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
            'acceptance_criteria': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ej. 1. El usuario recibe un correo.\n2. El enlace expira en 30 minutos.',
                    'rows': 5,
                }
            ),
            'requirement_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['project'].queryset = visible_projects_for(user).order_by('name')
        project_id = self.data.get('project') if self.is_bound else self.instance.project_id
        queryset = Requirement.objects.filter(project_id=project_id) if project_id else Requirement.objects.none()
        self.fields['code'].required = False
        self.fields['code'].disabled = True
        self.fields['code'].initial = self.instance.code or next_code(queryset, 'REQ')
        self.fields['code'].widget.attrs.update({
            'placeholder': 'REQ-001',
            'readonly': 'readonly',
            'data-default-code': 'REQ-001',
        })
        self.fields['status'].disabled = True
        self.fields['status'].help_text = 'El estado lo controla el flujo de revisión docente; no se puede cambiar desde el formulario.'
        self.fields['project'].widget.attrs.update({
            'data-code-target': self.fields['code'].widget.attrs.get('id', 'id_code'),
            'data-next-codes': json.dumps({
                str(project_id): next_code(Requirement.objects.filter(project_id=project_id), 'REQ')
                for project_id in Project.objects.values_list('id', flat=True)
            }),
        })
        help_texts = {
            'project': 'Proyecto donde se usara este requisito para trazabilidad y cobertura.',
            'code': 'Identificador unico del requisito, por ejemplo REQ-001.',
            'title': 'Nombre corto del comportamiento, regla o restriccion esperada.',
            'description': 'Describe con claridad que debe hacer el sistema y bajo que condiciones.',
            'acceptance_criteria': 'Escribe condiciones concretas y verificables. Usa una línea por criterio para derivar casos de prueba.',
            'requirement_type': 'Clasifica si el requisito es funcional, no funcional u otro tipo definido.',
            'priority': 'Indica la importancia del requisito para planificar pruebas y entregas.',
            'status': 'Pendiente: recien creado y aun no revisado. En revision: el responsable lo esta revisando. Aprobado: validado y listo para usarse en pruebas.',
        }
        for name, help_text in help_texts.items():
            self.fields[name].help_text = help_text
            self.fields[name].widget.attrs['data-help'] = help_text


class RequirementImportForm(forms.Form):
    project = forms.ModelChoiceField(
        queryset=Project.objects.none(),
        label='Proyecto',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    source_file = forms.FileField(
        label='Documento de requisitos',
        widget=forms.ClearableFileInput(
            attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.csv,.txt',
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        projects = kwargs.pop('projects', Project.objects.none())
        super().__init__(*args, **kwargs)
        self.fields['project'].queryset = projects
        self.fields['project'].help_text = 'Proyecto donde se cargaran los requisitos detectados.'
        self.fields['source_file'].help_text = (
            'Formatos admitidos: PDF, Word, Excel, CSV y TXT. Máximo 10 MB. Se recomienda una fila por requisito.'
        )

    def clean_source_file(self):
        source_file = self.cleaned_data['source_file']
        name = source_file.name.lower()
        allowed_extensions = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.csv', '.txt'}
        extension = '.' + name.rsplit('.', 1)[-1] if '.' in name else ''

        if extension not in allowed_extensions:
            raise forms.ValidationError('Usa un archivo PDF, Word, Excel, CSV o TXT.')

        if source_file.size > 10 * 1024 * 1024:
            raise forms.ValidationError('El documento no debe superar 10 MB.')

        return source_file
