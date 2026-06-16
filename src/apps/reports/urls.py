from django.urls import path

from apps.reports.views import report_delete_view, report_detail_view, report_download_view, report_list_view

app_name = 'reports'

urlpatterns = [
    path('', report_list_view, name='index'),
    path('<int:pk>/', report_detail_view, name='detail'),
    path('<int:pk>/download/', report_download_view, name='download'),
    path('<int:pk>/delete/', report_delete_view, name='delete'),
]
