from django.contrib import admin

from .models import TestPlan


@admin.register(TestPlan)
class TestPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'version', 'project', 'status', 'start_date', 'end_date')
    list_filter = ('status', 'project')
    search_fields = ('name', 'objective')
