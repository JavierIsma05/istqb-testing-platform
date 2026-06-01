from django.urls import path

from apps.executions.views import execution_workspace_view

app_name = 'executions'

urlpatterns = [
    path('', execution_workspace_view, name='index'),
]
