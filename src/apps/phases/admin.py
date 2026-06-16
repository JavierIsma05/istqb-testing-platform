from django.contrib import admin

from .models import TestingPhase


@admin.register(TestingPhase)
class TestingPhaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'order', 'status', 'progress', 'started_at', 'completed_at')
    list_filter = ('status', 'project')
    search_fields = ('name', 'description', 'entry_criteria', 'exit_criteria')
