from django.urls import path

from apps.defects.views import defect_create_view, defect_list_view

app_name = 'defects'

urlpatterns = [
    path('', defect_list_view, name='index'),
    path('new/', defect_create_view, name='create'),
]
