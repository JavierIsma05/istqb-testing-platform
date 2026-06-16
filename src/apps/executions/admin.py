from django.contrib import admin

from .models import AutomatedExecutionResult, AutomatedValidationRule, TestExecution, TestStepExecution


@admin.register(TestExecution)
class TestExecutionAdmin(admin.ModelAdmin):
    list_display = ('test_case', 'execution_mode', 'result', 'executed_by', 'executed_at')
    list_filter = ('execution_mode', 'result', 'review_status')
    search_fields = ('test_case__code', 'test_case__title', 'notes')


admin.site.register(TestStepExecution)
admin.site.register(AutomatedValidationRule)
admin.site.register(AutomatedExecutionResult)
