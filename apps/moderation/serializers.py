from rest_framework import serializers
from apps.moderation.models import ModerationQueue, ModerationLog
from apps.conversations.models import Response, ResponseApproval
from apps.users.serializers import UserDetailSerializer


class ModerationLogSerializer(serializers.ModelSerializer):
    moderator = UserDetailSerializer(read_only=True)

    class Meta:
        model = ModerationLog
        fields = ['id', 'moderator', 'action', 'notes', 'timestamp']
        read_only_fields = ['timestamp']


class ModerationQueueSerializer(serializers.ModelSerializer):
    response = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    project = serializers.SerializerMethodField()
    logs = ModerationLogSerializer(source='response.moderation_logs', many=True, read_only=True)

    class Meta:
        model = ModerationQueue
        fields = ['id', 'response', 'user', 'project', 'status', 'assigned_to', 'logs', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_response(self, obj):
        return {
            'id': obj.response.id,
            'content': obj.response.content,
            'status': obj.response.status,
            'created_at': obj.response.created_at
        }

    def get_user(self, obj):
        return {
            'id': obj.response.submitted_by.id,
            'email': obj.response.submitted_by.email,
            'name': f"{obj.response.submitted_by.first_name} {obj.response.submitted_by.last_name}"
        }

    def get_project(self, obj):
        return {
            'id': obj.response.message.conversation.project.id,
            'name': obj.response.message.conversation.project.name
        }


class ApprovalDecisionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=['approved', 'rejected'])
    comments = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        decision = data.get('decision')
        comments = data.get('comments', '')

        if decision == 'rejected' and not comments:
            raise serializers.ValidationError({'comments': 'Comments are required when rejecting.'})

        return data


class ModerationHistorySerializer(serializers.ModelSerializer):
    response_id = serializers.CharField(source='response.id', read_only=True)
    moderator = UserDetailSerializer(read_only=True)
    user = serializers.SerializerMethodField()

    class Meta:
        model = ModerationLog
        fields = ['id', 'response_id', 'moderator', 'user', 'action', 'notes', 'timestamp']

    def get_user(self, obj):
        return {
            'id': obj.response.submitted_by.id,
            'email': obj.response.submitted_by.email
        }
