from rest_framework import serializers
from apps.conversations.models import Conversation, Message, Response, ResponseApproval
from apps.users.serializers import UserDetailSerializer


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'role', 'content', 'tokens_used', 'is_submitted', 'timestamp']
        read_only_fields = ['id', 'tokens_used', 'timestamp']


class ConversationListSerializer(serializers.ModelSerializer):
    latest_message = serializers.SerializerMethodField()
    message_count = serializers.SerializerMethodField()
    user = UserDetailSerializer(read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'title', 'user', 'message_count', 'latest_message', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_latest_message(self, obj):
        latest = obj.message_set.last()
        return MessageSerializer(latest).data if latest else None

    def get_message_count(self, obj):
        return obj.message_set.count()


class ConversationDetailSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(source='message_set', many=True, read_only=True)
    message_count = serializers.SerializerMethodField()
    user = UserDetailSerializer(read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'title', 'summary', 'user', 'message_count', 'messages', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'messages']

    def get_message_count(self, obj):
        return obj.message_set.count()


class ConversationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ['title']


class ResponseApprovalSerializer(serializers.ModelSerializer):
    moderator = UserDetailSerializer(read_only=True)

    class Meta:
        model = ResponseApproval
        fields = ['id', 'moderator', 'decision', 'comments', 'crm_synced', 'approved_at']
        read_only_fields = ['id', 'moderator', 'approved_at']


class ResponseDetailSerializer(serializers.ModelSerializer):
    approval = ResponseApprovalSerializer(read_only=True)
    submitted_by = UserDetailSerializer(read_only=True)

    class Meta:
        model = Response
        fields = ['id', 'content', 'status', 'submitted_by', 'approval', 'created_at', 'updated_at']
        read_only_fields = ['id', 'submitted_by', 'created_at', 'updated_at', 'approval']


class ResponseListSerializer(serializers.ModelSerializer):
    approval = ResponseApprovalSerializer(read_only=True)

    class Meta:
        model = Response
        fields = ['id', 'content', 'status', 'approval', 'created_at']
        read_only_fields = fields


class ResponseSubmitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Response
        fields = ['message_id', 'content']

    def validate_message_id(self, value):
        try:
            message = Message.objects.get(id=value, role='assistant')
        except Message.DoesNotExist:
            raise serializers.ValidationError('Message does not exist or is not an assistant message.')

        if message.response:
            raise serializers.ValidationError('This message already has a response.')

        return value

    def create(self, validated_data):
        message = Message.objects.get(id=validated_data['message_id'])
        response = Response.objects.create(
            message=message,
            submitted_by=self.context['request'].user,
            content=validated_data['content'],
            status='submitted'
        )
        return response


class GenerateLLMResponseSerializer(serializers.Serializer):
    message_content = serializers.CharField(write_only=True)

    def validate_message_content(self, value):
        if not value.strip():
            raise serializers.ValidationError('Message content cannot be empty.')
        if len(value) > 4000:
            raise serializers.ValidationError('Message content is too long (max 4000 characters).')
        return value
