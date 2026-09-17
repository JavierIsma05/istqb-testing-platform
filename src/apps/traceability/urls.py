from django.urls import path

from apps.traceability.views import reopen_test_case_view, traceability_matrix_view
from apps.traceability.export import export_traceability_indicators_csv

app_name = 'traceability'

urlpatterns = [
    path('', traceability_matrix_view, name='index'),
    path('test-case/<int:pk>/reopen/', reopen_test_case_view, name='reopen-test-case'),
    path('export/indicators/csv/', export_traceability_indicators_csv, name='export-indicators-csv'),
]