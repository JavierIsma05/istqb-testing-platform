from django.urls import path

from apps.users.views.admin_views import (
    admin_dashboard_view,
    admin_project_create_view,
    admin_project_delete_view,
    admin_project_edit_view,
    admin_project_list_view,
    admin_user_create_view,
    admin_user_delete_view,
    admin_user_edit_view,
    admin_user_list_view,
)
from apps.users.views.profile_views import profile_view


app_name = 'users'

urlpatterns = [
    path('profile/', profile_view, name='profile'),
    path('admin-panel/', admin_dashboard_view, name='admin-dashboard'),
    path('admin-panel/usuarios/', admin_user_list_view, name='admin-users'),
    path('admin-panel/usuarios/nuevo/', admin_user_create_view, name='admin-user-create'),
    path('admin-panel/usuarios/<int:pk>/editar/', admin_user_edit_view, name='admin-user-edit'),
    path('admin-panel/usuarios/<int:pk>/eliminar/', admin_user_delete_view, name='admin-user-delete'),
    path('admin-panel/proyectos/', admin_project_list_view, name='admin-projects'),
    path('admin-panel/proyectos/nuevo/', admin_project_create_view, name='admin-project-create'),
    path('admin-panel/proyectos/<int:pk>/editar/', admin_project_edit_view, name='admin-project-edit'),
    path('admin-panel/proyectos/<int:pk>/eliminar/', admin_project_delete_view, name='admin-project-delete'),
]
