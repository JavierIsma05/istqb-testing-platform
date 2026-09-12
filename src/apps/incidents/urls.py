from django.urls import path

from apps.incidents.views import (
    incident_create_view,
    incident_delete_view,
    incident_list_view,
    incident_update_view,
    incident_transition_view,
)

app_name = 'incidents'

urlpatterns = [
    path('', incident_list_view, name='index'),
    path('new/', incident_create_view, name='create'),
    path('<int:pk>/edit/', incident_update_view, name='edit'),
    path('<int:pk>/transition/<str:status>/', incident_transition_view, name='transition'),
    path('<int:pk>/delete/', incident_delete_view, name='delete'),
]
