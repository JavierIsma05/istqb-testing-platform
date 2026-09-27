from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.audit.services import log_action
from apps.core.codes import next_code
from apps.core.permissions import admin_required
from apps.projects.forms import ProjectForm
from apps.projects.models import Project
from apps.projects.services import delete_project_and_related_data

from ..forms.admin_forms import AdminUserForm
from ..models import User


@admin_required
def admin_dashboard_view(request):
    users = User.objects.all()
    projects = Project.objects.select_related('tutor', 'created_by').prefetch_related('members')
    return render(request, 'adminpanel/dashboard.html', {
        'user_count': users.count(),
        'teacher_count': users.filter(role=User.Roles.TEACHER).count(),
        'student_count': users.filter(role=User.Roles.STUDENT).count(),
        'project_count': projects.count(),
        'recent_users': users.order_by('-date_joined')[:6],
        'recent_projects': projects.order_by('-updated_at', '-created_at')[:6],
    })


@admin_required
def admin_user_list_view(request):
    query = request.GET.get('q', '').strip()
    role = request.GET.get('role', '').strip()
    users = User.objects.all().order_by('role', 'last_name', 'first_name', 'email')
    if query:
        users = users.filter(Q(email__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query))
    if role in {choice[0] for choice in User.Roles.choices}:
        users = users.filter(role=role)
    return render(request, 'adminpanel/users.html', {
        'users': users,
        'query': query,
        'selected_role': role,
        'roles': User.Roles.choices,
    })


@admin_required
def admin_user_create_view(request):
    form = AdminUserForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        log_action(request.user, 'CREATE', 'User', user.pk, {'email': user.email, 'role': user.role})
        messages.success(request, f'Usuario {user.email} creado correctamente.')
        return redirect('users:admin-users')
    return render(request, 'adminpanel/user_form.html', {'form': form, 'title': 'Nuevo usuario', 'subtitle': 'Registra docentes, estudiantes o administradores del sistema.'})


@admin_required
def admin_user_edit_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    form = AdminUserForm(request.POST or None, instance=user)
    if request.method == 'POST' and form.is_valid():
        updated = form.save()
        log_action(request.user, 'UPDATE', 'User', updated.pk, {'email': updated.email, 'role': updated.role, 'is_active': updated.is_active})
        messages.success(request, f'Usuario {updated.email} actualizado correctamente.')
        return redirect('users:admin-users')
    return render(request, 'adminpanel/user_form.html', {'form': form, 'title': 'Editar usuario', 'subtitle': 'Actualiza datos, rol, estado o restablece la contraseña.', 'managed_user': user})


@admin_required
@require_POST
def admin_user_delete_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user.pk == request.user.pk:
        messages.error(request, 'No puedes eliminar tu propio usuario administrador.')
    elif user.role == User.Roles.ADMIN and User.objects.filter(role=User.Roles.ADMIN, is_active=True).count() <= 1:
        messages.error(request, 'Debe existir al menos un administrador activo.')
    else:
        email = user.email
        user.delete()
        log_action(request.user, 'DELETE', 'User', pk, {'email': email})
        messages.success(request, f'Usuario {email} eliminado.')
    return redirect('users:admin-users')


@admin_required
def admin_project_list_view(request):
    query = request.GET.get('q', '').strip()
    projects = Project.objects.select_related('created_by', 'tutor').prefetch_related('members').order_by('-updated_at', '-created_at')
    if query:
        projects = projects.filter(Q(code__icontains=query) | Q(name__icontains=query))
    return render(request, 'adminpanel/projects.html', {'projects': projects, 'query': query})


@admin_required
def admin_project_create_view(request):
    form = ProjectForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        project = form.save(commit=False)
        project.code = next_code(Project.objects.all(), 'PRJ')
        project.created_by = request.user
        project.save()
        project.members.set(form.cleaned_data.get('members', []))
        if form.cleaned_data.get('tutor'):
            project.tutor = form.cleaned_data['tutor']
            project.save(update_fields=['tutor', 'updated_at'])
            project.members.add(project.tutor)
        log_action(request.user, 'CREATE', 'Project', project.pk, {'code': project.code, 'name': project.name, 'source': 'admin_panel'})
        messages.success(request, f'Proyecto {project.code} creado correctamente.')
        return redirect('users:admin-projects')
    return render(request, 'projects/form.html', {'form': form, 'title': 'Nuevo proyecto administrativo', 'automatic_status_label': 'Planificado', 'subtitle': 'Crea un proyecto y asigna docentes y estudiantes sin entrar al módulo ISTQB.', 'admin_panel': True})


@admin_required
def admin_project_edit_view(request, pk):
    project = get_object_or_404(Project, pk=pk)
    form = ProjectForm(request.POST or None, instance=project)
    if request.method == 'POST' and form.is_valid():
        updated = form.save(commit=False)
        updated.tutor = form.cleaned_data.get('tutor')
        updated.save()
        updated.members.set(form.cleaned_data.get('members', []))
        if updated.tutor:
            updated.members.add(updated.tutor)
        log_action(request.user, 'UPDATE', 'Project', updated.pk, {'code': updated.code, 'name': updated.name, 'source': 'admin_panel'})
        messages.success(request, f'Proyecto {updated.code} actualizado correctamente.')
        return redirect('users:admin-projects')
    return render(request, 'projects/form.html', {'form': form, 'project': project, 'title': 'Editar proyecto administrativo', 'automatic_status_label': project.get_status_display(), 'subtitle': 'Administra los datos y las asignaciones del proyecto.', 'admin_panel': True})


@admin_required
@require_POST
def admin_project_delete_view(request, pk):
    project = get_object_or_404(Project, pk=pk)
    name = project.name
    delete_project_and_related_data(project)
    log_action(request.user, 'DELETE', 'Project', pk, {'name': name, 'source': 'admin_panel'})
    messages.success(request, f'Proyecto {name} y sus datos asociados fueron eliminados.')
    return redirect('users:admin-projects')
