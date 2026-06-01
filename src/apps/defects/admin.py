from django.contrib import admin

from .models import Defect


@admin.register(Defect)
class DefectAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'project', 'severity', 'priority', 'status', 'assigned_to')
    list_filter = ('severity', 'priority', 'status', 'project')
    search_fields = ('code', 'title', 'description')
