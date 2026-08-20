from django.contrib import admin
from apps.projects.models import Project, UserProject, ProjectArtifact


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


@admin.register(ProjectArtifact)
class ProjectArtifactAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'project', 'artifact_type', 'uploaded_by', 'size', 'created_at')
    list_filter = ('artifact_type', 'created_at')
    search_fields = ('file_name', 'project__name')
    readonly_fields = ('project', 'uploaded_by', 'artifact_type', 'file_name', 'content_type', 'size', 'created_at')
    exclude = ('content',)

    def has_add_permission(self, request):
        return False
