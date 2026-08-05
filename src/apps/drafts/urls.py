from django.urls import path

from .views import draft_clear_view, draft_get_view, draft_save_view

app_name = 'drafts'

urlpatterns = [
    path('save/', draft_save_view, name='save'),
    path('get/', draft_get_view, name='get'),
    path('clear/', draft_clear_view, name='clear'),
]
