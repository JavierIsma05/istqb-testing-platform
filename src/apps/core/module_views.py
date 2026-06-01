from django.contrib.auth.decorators import login_required
from django.forms import modelform_factory
from django.shortcuts import redirect, render

from apps.core.permissions import can_manage_artifacts, is_teacher, redirect_if_teacher_readonly, visible_projects_for
from apps.defects.models import Defect
from apps.executions.models import TestExecution
from apps.incidents.models import Incident
from apps.notifications.models import Notification
from apps.phases.models import TestingPhase
from apps.projects.models import Project
from apps.reports.models import Report
from apps.requirements.models import Requirement
from apps.testcases.models import TestCase
from apps.testplans.models import TestPlan
from apps.traceability.models import TraceabilityLink


MODULES = {
    'projects': {
        'title': 'Proyectos',
        'subtitle': 'Gestiona proyectos de prueba, miembros y estado general.',
        'model': Project,
        'columns': ('code', 'name', 'status'),
        'fields': ('code', 'name', 'description', 'status', 'start_date', 'end_date', 'members'),
        'namespace': 'projects',
    },
    'requirements': {
        'title': 'Requisitos',
        'subtitle': 'Centraliza requisitos funcionales y no funcionales trazables.',
        'model': Requirement,
        'columns': ('code', 'title', 'priority', 'status'),
        'fields': ('project', 'code', 'title', 'description', 'priority', 'status'),
        'namespace': 'requirements',
    },
    'testplans': {
        'title': 'Planes de prueba',
        'subtitle': 'Define objetivos, alcance, estrategia y aprobaciones.',
        'model': TestPlan,
        'columns': ('name', 'project', 'status'),
        'fields': ('project', 'name', 'objective', 'scope', 'strategy', 'status'),
        'namespace': 'testplans',
    },
    'testcases': {
        'title': 'Casos de prueba',
        'subtitle': 'Documenta pasos, resultados esperados y prioridad.',
        'model': TestCase,
        'columns': ('code', 'title', 'priority', 'status'),
        'fields': ('test_plan', 'requirement', 'code', 'title', 'preconditions', 'steps', 'expected_result', 'priority', 'status'),
        'namespace': 'testcases',
    },
    'executions': {
        'title': 'Ejecuciones',
        'subtitle': 'Registra resultados, evidencias y observaciones.',
        'model': TestExecution,
        'columns': ('test_case', 'result', 'executed_by'),
        'fields': ('test_case', 'executed_at', 'result', 'evidence', 'notes'),
        'namespace': 'executions',
    },
    'defects': {
        'title': 'Defectos',
        'subtitle': 'Da seguimiento a defectos desde reporte hasta cierre.',
        'model': Defect,
        'columns': ('title', 'project', 'severity', 'status'),
        'fields': ('project', 'execution', 'title', 'description', 'severity', 'status', 'assigned_to'),
        'namespace': 'defects',
    },
    'incidents': {
        'title': 'Incidentes',
        'subtitle': 'Controla eventos que afectan el ciclo de pruebas.',
        'model': Incident,
        'columns': ('title', 'project', 'status'),
        'fields': ('project', 'title', 'description', 'status'),
        'namespace': 'incidents',
    },
    'traceability': {
        'title': 'Trazabilidad',
        'subtitle': 'Relaciona requisitos con casos de prueba y cobertura.',
        'model': TraceabilityLink,
        'columns': ('requirement', 'test_case'),
        'fields': ('requirement', 'test_case', 'rationale'),
        'namespace': 'traceability',
    },
    'reports': {
        'title': 'Reportes',
        'subtitle': 'Prepara reportes de cobertura, defectos y ejecuciones.',
        'model': Report,
        'columns': ('title', 'project', 'report_type'),
        'fields': ('project', 'title', 'report_type'),
        'namespace': 'reports',
    },
    'notifications': {
        'title': 'Notificaciones',
        'subtitle': 'Consulta alertas y avisos de actividad relevante.',
        'model': Notification,
        'columns': ('title', 'recipient', 'is_read'),
        'fields': ('recipient', 'title', 'message', 'is_read', 'url'),
        'namespace': 'notifications',
    },
    'phases': {
        'title': 'Fases ISTQB',
        'subtitle': 'Organiza el avance por fases del proceso de pruebas.',
        'model': TestingPhase,
        'columns': ('name', 'project', 'order', 'status'),
        'fields': ('project', 'name', 'order', 'status', 'description'),
        'namespace': 'phases',
    },
}


@login_required
def module_index(request, module_key):
    module = MODULES[module_key]
    objects = module['model'].objects.all()
    visible_projects = visible_projects_for(request.user)

    if is_teacher(request.user):
        if module['model'] is Project:
            objects = objects.filter(id__in=visible_projects.values('id'))
        elif hasattr(module['model'], 'project'):
            objects = objects.filter(project__in=visible_projects)

    objects = objects[:25]

    return render(
        request,
        'components/module_index.html',
        {
            'module': module,
            'objects': objects,
            'columns': module['columns'],
            'create_url': f"{module['namespace']}:create",
            'can_manage': can_manage_artifacts(request.user),
        },
    )


@login_required
def module_create(request, module_key):
    module = MODULES[module_key]
    readonly_redirect = redirect_if_teacher_readonly(request, f"{module['namespace']}:index", module['title'].lower())
    if readonly_redirect:
        return readonly_redirect

    form_class = modelform_factory(module['model'], fields=module['fields'])
    form = form_class(request.POST or None, request.FILES or None)

    for field in form.fields.values():
        css_class = 'form-select' if getattr(field.widget, 'choices', None) else 'form-control'
        existing_class = field.widget.attrs.get('class', '')
        field.widget.attrs['class'] = f'{existing_class} {css_class}'.strip()

    if request.method == 'POST' and form.is_valid():
        instance = form.save(commit=False)
        if hasattr(instance, 'created_by_id'):
            instance.created_by = request.user
        if hasattr(instance, 'executed_by_id') and not instance.executed_by_id:
            instance.executed_by = request.user
        if hasattr(instance, 'reported_by_id') and not instance.reported_by_id:
            instance.reported_by = request.user
        if hasattr(instance, 'generated_by_id') and not instance.generated_by_id:
            instance.generated_by = request.user
        instance.save()
        form.save_m2m()
        return redirect(f"{module['namespace']}:index")

    return render(
        request,
        'components/module_form.html',
        {
            'module': module,
            'form': form,
        },
    )
