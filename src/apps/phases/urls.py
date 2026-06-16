from django.urls import path

from apps.phases.views import phase_advance_view, phase_list_view

app_name = 'phases'

urlpatterns = [
    path('', phase_list_view, name='index'),
    path('<int:pk>/advance/', phase_advance_view, name='advance'),
]
