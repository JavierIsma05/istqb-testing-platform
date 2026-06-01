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


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):

    list_display = (
        'full_name',
        'user',
    )