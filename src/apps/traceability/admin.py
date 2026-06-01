from django.contrib import admin

from .models import TraceabilityLink


@admin.register(TraceabilityLink)
class TraceabilityLinkAdmin(admin.ModelAdmin):
    list_display = ('requirement', 'test_case')
    search_fields = ('requirement__code', 'test_case__code', 'rationale')
