from django.contrib import admin

from .models import TestCase


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'test_plan', 'requirement', 'technique', 'level', 'priority', 'status')
    list_filter = ('technique', 'level', 'priority', 'status', 'test_plan')
    search_fields = ('code', 'title', 'steps', 'expected_result')
