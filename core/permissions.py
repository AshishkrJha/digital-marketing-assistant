from rest_framework import permissions


class IsUser(permissions.BasePermission):
    """User role permission."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'user'


class IsModerator(permissions.BasePermission):
    """Moderator or admin role permission."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['moderator', 'admin']


class IsAdmin(permissions.BasePermission):
    """Admin role permission."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class IsConversationOwner(permissions.BasePermission):
    """User owns the conversation."""
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsProjectMember(permissions.BasePermission):
    """User is a member of the project."""
    def has_object_permission(self, request, view, obj):
        from apps.projects.models import UserProject
        return UserProject.objects.filter(user=request.user, project=obj).exists()


class IsProjectOwnerOrAdmin(permissions.BasePermission):
    """User is the project owner or admin."""
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user or request.user.role == 'admin'


class IsResponseOwner(permissions.BasePermission):
    """User owns the response."""
    def has_object_permission(self, request, view, obj):
        return obj.submitted_by == request.user


class IsModeratorOrAdmin(permissions.BasePermission):
    """Only moderators and admins can access."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['moderator', 'admin']
