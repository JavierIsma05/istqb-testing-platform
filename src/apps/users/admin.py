from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, Profile


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    model = User

    list_display = (
        'email',
        'role',
        'is_staff',
        'is_active',
    )

    list_filter = (
        'role',
        'is_staff',
        'is_active',
    )

    ordering = ('email',)

    search_fields = ('email',)

    fieldsets = (
        (None, {
            'fields': (
                'email',
                'password',
                'role',
            )
        }),

        ('Permisos', {
            'fields': (
                'is_staff',
                'is_superuser',
                'is_active',
                'groups',
                'user_permissions',
            )
        }),

        ('Fechas importantes', {
            'fields': (
                'last_login',
                'date_joined',
            )
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),

            'fields': (
                'email',
                'password1',
                'password2',
                'role',
                'is_staff',
                'is_superuser',
                'is_active',
            ),
        }),
    )

    def _is_application_admin(self, request):
        return bool(
            getattr(request.user, 'is_authenticated', False)
            and getattr(request.user, 'role', None) == User.Roles.ADMIN
        )

    def has_module_permission(self, request):
        return self._is_application_admin(request)

    def has_view_permission(self, request, obj=None):
        return self._is_application_admin(request)

    def has_add_permission(self, request):
        return self._is_application_admin(request)

    def has_change_permission(self, request, obj=None):
        return self._is_application_admin(request)

    def has_delete_permission(self, request, obj=None):
        return self._is_application_admin(request)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):

    list_display = (
        'full_name',
        'user',
    )
