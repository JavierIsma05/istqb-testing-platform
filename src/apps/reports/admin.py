from django.contrib import admin

from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'report_type', 'generated_by', 'created_at')
    list_filter = ('report_type', 'project')
    search_fields = ('title',)
