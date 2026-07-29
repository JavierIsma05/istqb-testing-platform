from django.urls import path

from apps.executions.views import (
    automated_execution_run_view,
    automated_rule_create_view,
    automated_rule_delete_view,
    execution_calendar_view,
    execution_delete_view,
    execution_history_view,
    execution_workspace_view,
    teacher_api_projects,
    teacher_api_students,
    teacher_api_cases,
)

app_name = 'executions'

urlpatterns = [
    path('', execution_workspace_view, name='index'),
    path('calendar/', execution_calendar_view, name='calendar'),
    path('cases/<int:case_id>/history/', execution_history_view, name='history'),
    path('cases/<int:case_id>/rules/new/', automated_rule_create_view, name='rule-create'),
    path('cases/<int:case_id>/run-automated/', automated_execution_run_view, name='run-automated'),
    path('rules/<int:pk>/delete/', automated_rule_delete_view, name='rule-delete'),
    path('<int:pk>/delete/', execution_delete_view, name='delete'),
    path('api/projects/', teacher_api_projects, name='api-projects'),
    path('api/projects/<int:project_id>/students/', teacher_api_students, name='api-students'),
    path('api/projects/<int:project_id>/students/<int:student_id>/cases/', teacher_api_cases, name='api-cases'),
]
