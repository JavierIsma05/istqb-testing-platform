from django.urls import path

from .views import audit_export_csv_view, audit_list_view

app_name = 'audit'

urlpatterns = [
    path('', audit_list_view, name='index'),
    path('export.csv', audit_export_csv_view, name='export-csv'),
]
