from django.urls import path

from apps.traceability.views import traceability_matrix_view
from apps.traceability.export import export_traceability_indicators_csv

app_name = 'traceability'

urlpatterns = [
    path('', traceability_matrix_view, name='index'),
    path('export/indicators/csv/', export_traceability_indicators_csv, name='export-indicators-csv'),
]
