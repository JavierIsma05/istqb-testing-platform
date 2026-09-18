from django.contrib import admin

from .models import Project
from .services import delete_project_and_related_data


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'status', 'start_date', 'end_date')
    list_filter = ('status',)
    search_fields = ('code', 'name')

    def delete_queryset(self, request, queryset):
        """Usa el mismo borrado seguro que la interfaz de proyectos."""
        for project in queryset:
            delete_project_and_related_data(project)
