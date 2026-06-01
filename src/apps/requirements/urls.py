from django.urls import path

from apps.requirements.views import requirement_create_view, requirement_list_view

app_name = 'requirements'

urlpatterns = [
    path('', requirement_list_view, name='index'),
    path('new/', requirement_create_view, name='create'),
]
