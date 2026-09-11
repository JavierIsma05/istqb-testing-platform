from django.urls import path

from .views import audit_list_view

app_name = 'audit'

urlpatterns = [
    path('', audit_list_view, name='index'),
]
