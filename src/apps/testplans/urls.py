from django.urls import path

from apps.testplans.views import (
    testplan_create_view,
    testplan_delete_view,
    testplan_list_view,
    testplan_update_view,
)

app_name = 'testplans'

urlpatterns = [
    path('', testplan_list_view, name='index'),
    path('new/', testplan_create_view, name='create'),
    path('<int:pk>/edit/', testplan_update_view, name='edit'),
    path('<int:pk>/delete/', testplan_delete_view, name='delete'),
]
