from django.urls import path

from apps.testcases.views import (
    testcase_delete_view,
    testcase_detail_view,
    testcase_list_view,
    testcase_update_view,
)

app_name = 'testcases'

urlpatterns = [
    path('', testcase_list_view, name='index'),
    path('<int:pk>/', testcase_detail_view, name='detail'),
    path('<int:pk>/edit/', testcase_update_view, name='edit'),
    path('<int:pk>/delete/', testcase_delete_view, name='delete'),
]
