from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.audit.services import log_action
from apps.core.permissions import (
    can_manage_artifacts,
    get_active_project_for_request,
    is_teacher,
    redirect_if_teacher_readonly,
    visible_projects_for,
)
from apps.core.codes import next_code
from apps.core.lifecycle import defect_transition_allowed, defect_transition_options

from .forms import DefectForm
from .history import record_defect_history
from .models import Defect

STATUS_BADGES = {
    Defect.Status.OPEN: 'open', Defect.Status.ANALYSIS: 'info', Defect.Status.IN_PROGRESS: 'warning',
    Defect.Status.RESOLVED: 'info', Defect.Status.PENDING_CONFIRMATION: 'warning', Defect.Status.CLOSED: 'success',
    Defect.Status.REOPENED: 'warning', Defect.Status.REJECTED: 'muted', Defect.Status.DUPLICATED: 'muted',
}
SEVERITY_BADGES = {Defect.Severity.HIGH: 'danger', Defect.Severity.MEDIUM: 'medium', Defect.Severity.LOW: 'low'}
PRIORITY_BADGES = {Defect.Priority.CRITICAL: 'danger', Defect.Priority.HIGH: 'high', Defect.Priority.MEDIUM: 'medium', Defect.Priority.LOW: 'low'}

PRIMARY_DEFECT_ACTIONS = {
    Defect.Status.OPEN: ('ANALYSIS', 'Enviar a análisis', 'bi-arrow-right-circle', ''),
    Defect.Status.ANALYSIS: ('IN_PROGRESS', 'Iniciar corrección', 'bi-tools', ''),
    Defect.Status.IN_PROGRESS: ('RESOLVED', 'Marcar como resuelto', 'bi-check2-circle', ''),
    Defect.Status.RESOLVED: ('PENDING_CONFIRMATION', 'Solicitar confirmación', 'bi-shield-check', ''),
    Defect.Status.PENDING_CONFIRMATION: ('CLOSED', 'Cerrar defecto', 'bi-lock', 'Solo se puede cerrar después de una confirmación aprobada.'),
    Defect.Status.REOPENED: ('IN_PROGRESS', 'Retomar corrección', 'bi-tools', ''),
}
SECONDARY_LABELS = {
    Defect.Status.OPEN: {'ANALYSIS': 'Enviar a análisis', 'IN_PROGRESS': 'Iniciar corrección', 'REJECTED': 'Rechazar', 'DUPLICATED': 'Marcar como duplicado'},
    Defect.Status.ANALYSIS: {'IN_PROGRESS': 'Iniciar corrección', 'OPEN': 'Volver a abierto'},
    Defect.Status.IN_PROGRESS: {'RESOLVED': 'Marcar como resuelto', 'OPEN': 'Volver a abierto'},
    Defect.Status.RESOLVED: {'PENDING_CONFIRMATION': 'Solicitar confirmación', 'IN_PROGRESS': 'Volver a corrección', 'REOPENED': 'Reabrir defecto'},
    Defect.Status.PENDING_CONFIRMATION: {'CLOSED': 'Cerrar defecto', 'REOPENED': 'Reabrir defecto'},
    Defect.Status.CLOSED: {'REOPENED': 'Reabrir defecto'},
    Defect.Status.REOPENED: {'IN_PROGRESS': 'Retomar corrección', 'REJECTED': 'Rechazar'},
}


def _defect_actions(defect):
    options = list(defect_transition_options(defect.status))
    primary = PRIMARY_DEFECT_ACTIONS.get(defect.status)
    primary_status = None
    primary_label = None
    primary_icon = None
    primary_confirm = None
    if primary and primary[0] in options:
        primary_status, primary_label, primary_icon, primary_confirm = primary
        if primary_status == Defect.Status.CLOSED and not (
            defect.verification_execution_id
            and defect.verification_execution.result == 'PASSED'
            and defect.verification_execution.execution_type == 'CONFIRMATION'
        ):
            primary_status = None
            primary_label = None
            primary_icon = None
            primary_confirm = None

    secondary_statuses = []
    labels = SECONDARY_LABELS.get(defect.status, {})
    for status in options:
        if status == primary_status:
            continue
        label = labels.get(status)
        if label:
            secondary_statuses.append({'status': status, 'label': label, 'icon': 'bi-arrow-right-circle'})

    return {
        'primary_status': primary_status,
        'primary_label': primary_label,
        'primary_icon': primary_icon,
        'primary_confirm': primary_confirm,
        'secondary_statuses': secondary_statuses,
    }


@login_required
def defect_list_view(request):
    query = request.GET.get('q', '').strip(); project_id = request.GET.get('project', '').strip(); status = request.GET.get('status', '').strip()
    visible_projects = visible_projects_for(request.user, request=request); active_project = get_active_project_for_request(request)
    defects = Defect.objects.select_related('project','reported_by','assigned_to','execution','execution__test_case','verification_execution').annotate(history_count=Count('history', distinct=True)).filter(project__in=visible_projects)
    if query: defects = defects.filter(Q(code__icontains=query)|Q(title__icontains=query)|Q(description__icontains=query))
    if active_project: defects = defects.filter(project=active_project)
    elif project_id: defects = defects.filter(project_id=project_id)
    if status: defects = defects.filter(status=status)
    items=[]
    for defect in defects:
        item={'defect':defect,'badge':STATUS_BADGES.get(defect.status,'muted'),'severity_badge':SEVERITY_BADGES.get(defect.severity,'muted'),'priority_badge':PRIORITY_BADGES.get(defect.priority,'muted'),'next_statuses':defect_transition_options(defect.status)}
        item.update(_defect_actions(defect)); items.append(item)
    return render(request,'defects/index.html',{
        'items':items,'total':defects.count(),'open_count':defects.filter(status=Defect.Status.OPEN).count(),'in_fix_count':defects.filter(status=Defect.Status.IN_PROGRESS).count(),
        'resolved_count':defects.filter(status=Defect.Status.RESOLVED).count(),'reopened_count':defects.filter(status=Defect.Status.REOPENED).count(),'closed_count':defects.filter(status=Defect.Status.CLOSED).count(),
        'projects':visible_projects.order_by('name'),'status_choices':Defect.Status.choices,'selected_project':project_id,'selected_status':status,'query':query,'can_manage':can_manage_artifacts(request.user),
    })

@login_required
def defect_create_view(request):
    readonly_redirect = redirect_if_teacher_readonly(request,'defects:index','defectos')
    if readonly_redirect: return readonly_redirect
    form = DefectForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        defect=form.save(commit=False); defect.code=next_code(Defect.objects.filter(project=defect.project),'DEF'); defect.reported_by=request.user; defect.save(); record_defect_history(defect,request.user,'Registro inicial del defecto')
        log_action(request.user,'CREATE','Defect',defect.pk,{'project_id':defect.project_id,'code':defect.code,'title':defect.title,'status':defect.status}); messages.success(request,'Defecto registrado correctamente.'); return redirect('defects:index')
    return render(request,'defects/form.html',{'form':form,'title':'Reportar Defecto','subtitle':'Registra y asigna defectos encontrados durante la ejecución de pruebas.'})

@login_required
def defect_update_view(request, pk):
    readonly_redirect=redirect_if_teacher_readonly(request,'defects:index','defectos')
    if readonly_redirect: return readonly_redirect
    defect=get_object_or_404(Defect,pk=pk,project__in=visible_projects_for(request.user,request=request)); form=DefectForm(request.POST or None,instance=defect,user=request.user)
    if request.method=='POST' and form.is_valid():
        defect=form.save(); record_defect_history(defect,request.user,'Actualizacion del defecto'); log_action(request.user,'UPDATE','Defect',defect.pk,{'project_id':defect.project_id,'code':defect.code,'title':defect.title,'status':defect.status}); messages.success(request,'Defecto actualizado correctamente.'); return redirect('defects:index')
    return render(request,'defects/form.html',{'form':form,'title':'Editar Defecto','subtitle':'Actualiza la severidad o la descripción del defecto sin perder su historial ni su vínculo con el caso de prueba.'})

@login_required
@require_POST
def defect_delete_view(request, pk):
    readonly_redirect=redirect_if_teacher_readonly(request,'defects:index','defectos')
    if readonly_redirect: return readonly_redirect
    defect=get_object_or_404(Defect,pk=pk,project__in=visible_projects_for(request.user,request=request))
    if defect.history.exists() or defect.execution_id is not None or defect.verification_execution_id is not None:
        messages.error(request,'El defecto tiene historial o trazabilidad asociada y no puede eliminarse. Cambia su estado para conservar el registro.'); return redirect('defects:index')
    log_action(request.user,'DELETE','Defect',defect.pk,{'project_id':defect.project_id,'code':defect.code,'title':defect.title,'status':defect.status}); defect.delete(); messages.success(request,'Defecto eliminado correctamente.')
    return redirect('defects:index')

@login_required
@require_POST
def defect_transition_view(request, pk, status=None):
    readonly_redirect=redirect_if_teacher_readonly(request,'defects:index','defectos')
    if readonly_redirect: return readonly_redirect
    defect=get_object_or_404(Defect,pk=pk,project__in=visible_projects_for(request.user,request=request))
    target=status
    if not target: messages.error(request,'Debes seleccionar un estado de destino para la transición.'); return redirect('defects:index')
    if target == Defect.Status.IN_PROGRESS and not defect.assigned_to: defect.assigned_to=request.user
    try: defect_transition_allowed(defect,target)
    except ValidationError as exc: messages.error(request,str(exc)); return redirect('defects:index')
    defect.status=target; defect.save(update_fields=['status','assigned_to','updated_at'])
    reason={Defect.Status.OPEN:'Transición a Abierto',Defect.Status.IN_PROGRESS:'Transición a En progreso',Defect.Status.RESOLVED:'Transición a Resuelto',Defect.Status.PENDING_CONFIRMATION:'Transición a Pendiente de confirmación',Defect.Status.CLOSED:'Cierre por confirmación',Defect.Status.REOPENED:'Reapertura del defecto',Defect.Status.ANALYSIS:'Transición a En análisis',Defect.Status.REJECTED:'Defecto rechazado',Defect.Status.DUPLICATED:'Defecto marcado como duplicado'}.get(target,'Transición de estado')
    record_defect_history(defect,request.user,reason); log_action(request.user,'UPDATE','Defect',defect.pk,{'project_id':defect.project_id,'code':defect.code,'title':defect.title,'status':defect.status}); messages.success(request,f'Estado actualizado a {defect.get_status_display()}.')
    return redirect('defects:index')