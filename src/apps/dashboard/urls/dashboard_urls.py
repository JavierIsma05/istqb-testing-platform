from django.urls import path

from apps.dashboard.views.dashboard_views import (
    dashboard_view,
    phase_progress_view,
)

urlpatterns = [
    path('phase-progress/', phase_progress_view, name='phase-progress'),

    path(
        '',
        dashboard_view,
        name='dashboard'
    ),

]
