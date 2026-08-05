from django.urls import path

from apps.defects.views import (
    defect_create_view,
    defect_delete_view,
    defect_list_view,
    defect_transition_view,
    defect_update_view,
)

app_name = 'defects'

urlpatterns = [
    path('', defect_list_view, name='index'),
    path('new/', defect_create_view, name='create'),
    path('<int:pk>/edit/', defect_update_view, name='edit'),
    path('<int:pk>/delete/', defect_delete_view, name='delete'),
    path('<int:pk>/transition/', defect_transition_view, name='transition'),
]
