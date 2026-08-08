from django.contrib import admin
from apps.projects.models import Project, UserProject


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'owner__email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserProject)
class UserProjectAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'role', 'joined_at')
    list_filter = ('role', 'joined_at')
    search_fields = ('user__email', 'project__name')
    readonly_fields = ('joined_at',)
