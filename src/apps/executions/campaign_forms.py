from django import forms

from apps.core.permissions import visible_projects_for
from apps.testcases.models import TestCase
from apps.testplans.models import TestPlan

from .models import BuildArtifact, TestRun


class BuildArtifactForm(forms.ModelForm):
    class Meta:
        model = BuildArtifact
        fields = ('project', 'version', 'build_number', 'commit_sha', 'branch', 'repository_url', 'environment', 'checksum', 'release_notes')
        widgets = {field: forms.TextInput(attrs={'class': 'form-control'}) for field in fields if field not in ('project', 'environment', 'release_notes')}
        widgets.update({
            'project': forms.Select(attrs={'class': 'form-select'}),
            'environment': forms.Select(attrs={'class': 'form-select'}),
            'release_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        })

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['project'].queryset = visible_projects_for(user) if user else self.fields['project'].queryset.none()


class TestRunForm(forms.ModelForm):
    class Meta:
        model = TestRun
        fields = ('project', 'test_plan', 'build', 'name', 'run_type', 'environment', 'scope', 'test_cases')
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'test_plan': forms.Select(attrs={'class': 'form-select'}),
            'build': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'run_type': forms.Select(attrs={'class': 'form-select'}),
            'environment': forms.TextInput(attrs={'class': 'form-control'}),
            'scope': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'test_cases': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 10}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        projects = visible_projects_for(user) if user else self.fields['project'].queryset.none()
        self.fields['project'].queryset = projects
        self.fields['test_plan'].queryset = TestPlan.objects.filter(project__in=projects, status=TestPlan.Status.APPROVED).order_by('name')
        self.fields['build'].queryset = BuildArtifact.objects.filter(project__in=projects).order_by('-created_at')
        self.fields['test_cases'].queryset = TestCase.objects.filter(test_plan__project__in=projects).order_by('test_plan', 'code')

    def clean(self):
        cleaned = super().clean()
        project = cleaned.get('project')
        plan = cleaned.get('test_plan')
        build = cleaned.get('build')
        cases = cleaned.get('test_cases')
        if plan and project and plan.project_id != project.pk:
            self.add_error('test_plan', 'El plan debe pertenecer al proyecto seleccionado.')
        if build and project and build.project_id != project.pk:
            self.add_error('build', 'La build debe pertenecer al proyecto seleccionado.')
        if plan and cases and any(case.test_plan_id != plan.pk for case in cases):
            self.add_error('test_cases', 'Todos los casos deben pertenecer al plan seleccionado.')
        if not cases:
            self.add_error('test_cases', 'Selecciona al menos un caso para la campaña.')
        return cleaned
