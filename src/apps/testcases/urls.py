from django.urls import path

from apps.testcases.views import testcase_list_view

app_name = 'testcases'

urlpatterns = [
    path('', testcase_list_view, name='index'),
]
