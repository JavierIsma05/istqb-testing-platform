from django.urls import path

from apps.reports.views import (
    plan_defects_report_view,
    plan_executions_report_view,
    plan_final_report_view,
    plan_report_dashboard_view,
    plan_report_pdf_view,
    plan_report_selector_view,
    plan_report_view,
    plan_testcases_report_view,
    report_delete_view,
    report_detail_view,
    report_download_view,
    report_list_view,
)

app_name = 'reports'

urlpatterns = [
    path('', report_list_view, name='index'),
    path('plan-report/', plan_report_selector_view, name='plan-report'),
    path('plan-report/<int:pk>/', plan_report_view, name='plan-report-detail'),
    path('plan/<int:pk>/', plan_report_dashboard_view, name='plan-dashboard'),
    path('plan/<int:pk>/casos/', plan_testcases_report_view, name='plan-casos'),
    path('plan/<int:pk>/ejecuciones/', plan_executions_report_view, name='plan-ejecuciones'),
    path('plan/<int:pk>/defectos/', plan_defects_report_view, name='plan-defectos'),
    path('plan/<int:pk>/final/', plan_final_report_view, name='plan-final'),
    path('plan/<int:pk>/pdf/<slug:section>/', plan_report_pdf_view, name='plan-pdf'),
    path('<int:pk>/', report_detail_view, name='detail'),
    path('<int:pk>/download/', report_download_view, name='download'),
    path('<int:pk>/delete/', report_delete_view, name='delete'),
]
