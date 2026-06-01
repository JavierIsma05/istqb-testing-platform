from django.urls import path

from apps.phases.views import phase_list_view

app_name = 'phases'

urlpatterns = [
    path('', phase_list_view, name='index'),
]
