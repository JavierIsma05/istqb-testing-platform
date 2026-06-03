from django.urls import path

from apps.users.views.profile_views import profile_view


app_name = 'users'

urlpatterns = [
    path('profile/', profile_view, name='profile'),
]
