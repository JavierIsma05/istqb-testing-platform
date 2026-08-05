from django.urls import path

from apps.projects.views import (
    project_create_view,
    project_delete_view,
    project_detail_view,
    project_edit_view,
    project_list_view,
)

app_name = 'projects'

urlpatterns = [
    path('', project_list_view, name='index'),
    path('new/', project_create_view, name='create'),
    path('<int:pk>/edit/', project_edit_view, name='edit'),
    path('<int:pk>/delete/', project_delete_view, name='delete'),
    path('<int:pk>/', project_detail_view, name='detail'),
]
