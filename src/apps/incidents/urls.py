from django.urls import path

from apps.incidents.views import incident_create_view, incident_list_view

app_name = 'incidents'

urlpatterns = [
    path('', incident_list_view, name='index'),
    path('new/', incident_create_view, name='create'),
]
