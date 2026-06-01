from django.contrib import admin

from .models import TestExecution


@admin.register(TestExecution)
class TestExecutionAdmin(admin.ModelAdmin):
    list_display = ('test_case', 'result', 'executed_by', 'executed_at')
    list_filter = ('result',)
    search_fields = ('test_case__code', 'test_case__title', 'notes')
