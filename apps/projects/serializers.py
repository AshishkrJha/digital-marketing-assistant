from rest_framework import serializers
from apps.projects.models import Project, UserProject
from apps.users.serializers import UserDetailSerializer


class UserProjectSerializer(serializers.ModelSerializer):
    user = UserDetailSerializer(read_only=True)

    class Meta:
        model = UserProject
        fields = ['id', 'user', 'role', 'joined_at']


class ProjectListSerializer(serializers.ModelSerializer):
    owner = UserDetailSerializer(read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'owner', 'is_active', 'created_at']
        read_only_fields = ['id', 'owner', 'created_at']


class ProjectDetailSerializer(serializers.ModelSerializer):
    owner = UserDetailSerializer(read_only=True)
    members = UserProjectSerializer(source='members', many=True, read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'owner', 'is_active', 'members', 'member_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    def get_member_count(self, obj):
        return obj.members.count() + 1  # +1 for owner


class ProjectCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['name', 'description', 'is_active']


class AddProjectMemberSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    role = serializers.ChoiceField(choices=['member', 'admin'])

    def validate_user_id(self, value):
        from apps.users.models import User
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('User does not exist.')
        return value
