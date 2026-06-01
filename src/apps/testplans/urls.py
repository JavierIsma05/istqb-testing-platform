from django.urls import path

from apps.testplans.views import testplan_create_view, testplan_list_view

app_name = 'testplans'

urlpatterns = [
    path('', testplan_list_view, name='index'),
    path('new/', testplan_create_view, name='create'),
]
