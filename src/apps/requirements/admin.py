from django.contrib import admin

from .models import Requirement


@admin.register(Requirement)
class RequirementAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'project', 'requirement_type', 'priority', 'status')
    list_filter = ('requirement_type', 'priority', 'status', 'project')
    search_fields = ('code', 'title', 'description')
