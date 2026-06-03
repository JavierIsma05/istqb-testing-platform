from django.urls import path

from apps.requirements.views import (
    requirement_create_view,
    requirement_delete_view,
    requirement_list_view,
    requirement_update_view,
)

app_name = 'requirements'

urlpatterns = [
    path('', requirement_list_view, name='index'),
    path('new/', requirement_create_view, name='create'),
    path('<int:pk>/edit/', requirement_update_view, name='edit'),
    path('<int:pk>/delete/', requirement_delete_view, name='delete'),
]
