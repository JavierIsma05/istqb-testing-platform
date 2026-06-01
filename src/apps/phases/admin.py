from django.contrib import admin

from .models import TestingPhase


@admin.register(TestingPhase)
class TestingPhaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'order', 'status', 'progress')
    list_filter = ('status', 'project')
    search_fields = ('name', 'description')
