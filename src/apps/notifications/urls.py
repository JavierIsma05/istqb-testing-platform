from django.urls import path

from apps.notifications.views import (
    notification_list_view,
    notification_mark_all_read_view,
    notification_mark_read_view,
    send_project_message_view,
)

app_name = 'notifications'

urlpatterns = [
    path('', notification_list_view, name='index'),
    path('send-project-message/', send_project_message_view, name='send_project_message'),
    path('<int:pk>/read/', notification_mark_read_view, name='mark_read'),
    path('read-all/', notification_mark_all_read_view, name='mark_all_read'),
]
