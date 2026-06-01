from django.urls import path

from apps.traceability.views import traceability_matrix_view

app_name = 'traceability'

urlpatterns = [
    path('', traceability_matrix_view, name='index'),
]
