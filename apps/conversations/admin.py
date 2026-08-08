from django.contrib import admin
from apps.conversations.models import Conversation, Message, Response, ResponseApproval


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'project', 'title', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__email', 'project__name', 'title')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'role', 'is_submitted', 'timestamp')
    list_filter = ('role', 'is_submitted', 'timestamp')
    search_fields = ('conversation__title', 'content')
    readonly_fields = ('timestamp',)


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ('id', 'submitted_by', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('submitted_by__email', 'content')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ResponseApproval)
class ResponseApprovalAdmin(admin.ModelAdmin):
    list_display = ('id', 'response', 'moderator', 'decision', 'crm_synced', 'approved_at')
    list_filter = ('decision', 'crm_synced', 'approved_at')
    search_fields = ('moderator__email', 'response__id')
    readonly_fields = ('approved_at', 'updated_at')
