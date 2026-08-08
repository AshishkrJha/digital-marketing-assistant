from django.contrib import admin
from apps.integrations.models import GeminiLog, CRMLog


@admin.register(GeminiLog)
class GeminiLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'total_tokens', 'model', 'timestamp')
    list_filter = ('model', 'timestamp')
    search_fields = ('conversation__id',)
    readonly_fields = ('timestamp',)


@admin.register(CRMLog)
class CRMLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'response', 'status', 'response_code', 'attempt_count', 'last_attempt_at')
    list_filter = ('status', 'last_attempt_at')
    search_fields = ('response__id', 'webhook_url')
    readonly_fields = ('created_at', 'updated_at')
