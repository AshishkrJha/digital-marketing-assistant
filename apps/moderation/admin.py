from django.contrib import admin
from apps.moderation.models import ModerationQueue, ModerationLog


@admin.register(ModerationQueue)
class ModerationQueueAdmin(admin.ModelAdmin):
    list_display = ('id', 'response', 'status', 'assigned_to', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('response__id', 'assigned_to__email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ModerationLog)
class ModerationLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'response', 'moderator', 'action', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('response__id', 'moderator__email')
    readonly_fields = ('timestamp',)
