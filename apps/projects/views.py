from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.projects.models import Project, UserProject
from apps.projects.serializers import (
    ProjectListSerializer,
    ProjectDetailSerializer,
    ProjectCreateUpdateSerializer,
    UserProjectSerializer,
    AddProjectMemberSerializer,
)
from core.permissions import IsProjectOwnerOrAdmin, IsProjectMember
from core.exceptions import InvalidProjectAccess


class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_active']
    ordering_fields = ['-created_at']

    def get_queryset(self):
        """Return projects owned by or member of current user."""
        user = self.request.user
        owned = Project.objects.filter(owner=user)
        member = Project.objects.filter(userproject__user=user)
        return (owned | member).distinct().order_by('-created_at')

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProjectCreateUpdateSerializer
        elif self.action == 'retrieve':
            return ProjectDetailSerializer
        return ProjectListSerializer

    def create(self, request, *args, **kwargs):
        """Create a new project (current user becomes owner)."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = serializer.save(owner=request.user)
        return Response(
            ProjectDetailSerializer(project).data,
            status=status.HTTP_201_CREATED
        )

    def perform_update(self, serializer):
        """Only owner can update project."""
        project = self.get_object()
        if project.owner != self.request.user:
            raise InvalidProjectAccess('Only project owner can update.')
        serializer.save()

    def perform_destroy(self, instance):
        """Only owner can delete project."""
        if instance.owner != self.request.user:
            raise InvalidProjectAccess('Only project owner can delete.')
        instance.delete()

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def members(self, request, pk=None):
        """Get all members of a project."""
        try:
            project = self.get_object()
        except Project.DoesNotExist:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        members = project.members.all()
        serializer = UserProjectSerializer(members, many=True)

        return Response({
            'owner': project.owner.email,
            'members': serializer.data
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_member(self, request, pk=None):
        """Add a member to the project (owner only)."""
        try:
            project = self.get_object()
        except Project.DoesNotExist:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if project.owner != request.user:
            return Response(
                {'error': 'Only project owner can add members'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AddProjectMemberSerializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            role = serializer.validated_data['role']

            from apps.users.models import User
            user = User.objects.get(id=user_id)

            user_project, created = UserProject.objects.get_or_create(
                user=user,
                project=project,
                defaults={'role': role}
            )

            if not created:
                user_project.role = role
                user_project.save()

            return Response(
                UserProjectSerializer(user_project).data,
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def remove_member(self, request, pk=None):
        """Remove a member from the project (owner only)."""
        try:
            project = self.get_object()
        except Project.DoesNotExist:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if project.owner != request.user:
            return Response(
                {'error': 'Only project owner can remove members'},
                status=status.HTTP_403_FORBIDDEN
            )

        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user_project = UserProject.objects.get(user_id=user_id, project=project)
            user_project.delete()
            return Response(
                {'message': 'Member removed successfully'},
                status=status.HTTP_200_OK
            )
        except UserProject.DoesNotExist:
            return Response(
                {'error': 'User is not a member of this project'},
                status=status.HTTP_404_NOT_FOUND
            )
