from django.contrib import admin

from .models import (
    AutomatedExecutionResult,
    AutomatedValidationRule,
    TestData,
    TestExecution,
    TestStepExecution,
)


@admin.register(TestExecution)
class TestExecutionAdmin(admin.ModelAdmin):
    list_display = ('test_case', 'execution_mode', 'result', 'executed_by', 'executed_at')
    list_filter = ('execution_mode', 'result', 'review_status')
    search_fields = ('test_case__code', 'test_case__title', 'notes')


@admin.register(TestData)
class TestDataAdmin(admin.ModelAdmin):
    list_display = ('test_case', 'key', 'value')
    list_filter = ('test_case__test_plan__project',)
    search_fields = ('test_case__code', 'key', 'value')
    autocomplete_fields = ('test_case',)


@admin.register(AutomatedValidationRule)
class AutomatedValidationRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'test_case', 'step_number', 'action_type', 'comparison_type', 'is_active')
    list_filter = ('action_type', 'comparison_type', 'is_active')
    search_fields = ('name', 'test_case__code')


@admin.register(AutomatedExecutionResult)
class AutomatedExecutionResultAdmin(admin.ModelAdmin):
    list_display = ('validation_rule', 'test_execution', 'status', 'comparison_type')
    list_filter = ('status', 'comparison_type')
    search_fields = ('validation_rule__name', 'test_execution__test_case__code')


admin.site.register(TestStepExecution)
