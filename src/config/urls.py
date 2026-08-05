from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.core.views import landing_view

urlpatterns = [
    path('', landing_view, name='landing'),

    path(
        'admin/',
        admin.site.urls
    ),

    path(
        'dashboard/',
        include('apps.dashboard.urls.dashboard_urls')
    ),
    path(
        '',
        include('apps.authentication.urls.auth_urls')
    ),
    path('projects/', include('apps.projects.urls')),
    path('requirements/', include('apps.requirements.urls')),
    path('test-plans/', include('apps.testplans.urls')),
    path('test-cases/', include('apps.testcases.urls')),
    path('executions/', include('apps.executions.urls')),
    path('defects/', include('apps.defects.urls')),
    path('incidents/', include('apps.incidents.urls')),
    path('traceability/', include('apps.traceability.urls')),
    path('reports/', include('apps.reports.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('phases/', include('apps.phases.urls')),
    path('drafts/', include('apps.drafts.urls')),
    path('', include('apps.users.urls.user_urls')),

]

if settings.DEBUG:

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
