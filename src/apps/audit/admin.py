from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'entity', 'entity_id', 'actor', 'created_at')
    list_filter = ('action', 'entity')
    search_fields = ('action', 'entity', 'entity_id', 'actor__email')
    readonly_fields = ('actor', 'action', 'entity', 'entity_id', 'metadata', 'created_at', 'updated_at')
    ordering = ('-created_at', '-id')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
