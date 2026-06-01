from django.contrib import admin

from .models import Incident


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'project', 'probability', 'impact', 'status', 'reported_by', 'created_at')
    list_filter = ('probability', 'impact', 'status', 'project')
    search_fields = ('code', 'title', 'description')
