from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from apps.conversations.models import Conversation, Message, Response as ResponseModel, ResponseApproval
from apps.conversations.serializers import (
    ConversationListSerializer,
    ConversationDetailSerializer,
    ConversationCreateSerializer,
    MessageSerializer,
    ResponseSubmitSerializer,
    ResponseDetailSerializer,
    ResponseListSerializer,
    GenerateLLMResponseSerializer,
)
from core.exceptions import InvalidProjectAccess, LLMAPIError
from core.utils import get_project_or_forbidden, log_moderation_action
import logging

logger = logging.getLogger('llm')


class ConversationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    ordering_fields = ['-created_at']

    def get_queryset(self):
        """Return conversations for current user."""
        return Conversation.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return ConversationCreateSerializer
        elif self.action == 'retrieve':
            return ConversationDetailSerializer
        return ConversationListSerializer

    def create(self, request, *args, **kwargs):
        """Create a new conversation."""
        project_id = request.query_params.get('project_id')

        if not project_id:
            return Response(
                {'error': 'project_id query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            project = get_project_or_forbidden(project_id, request.user)
        except InvalidProjectAccess as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        conversation = Conversation.objects.create(
            user=request.user,
            project=project,
            title=serializer.validated_data.get('title', '')
        )

        return Response(
            ConversationDetailSerializer(conversation).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def generate_response(self, request, pk=None):
        """Generate LLM response using LangChain."""
        conversation = self.get_object()

        serializer = GenerateLLMResponseSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_message_content = serializer.validated_data['message_content']

        try:
            # Create user message
            user_message = Message.objects.create(
                conversation=conversation,
                role='user',
                content=user_message_content
            )

            # Generate LLM response using LangChain service
            from apps.integrations.llm_service import generate_llm_response

            llm_response_content = generate_llm_response(
                conversation_id=conversation.id,
                user_message=user_message_content,
                conversation_obj=conversation
            )

            # Create assistant message
            assistant_message = Message.objects.create(
                conversation=conversation,
                role='assistant',
                content=llm_response_content
            )

            # Update conversation title if not set
            if not conversation.title:
                conversation.title = user_message_content[:50] + '...' if len(user_message_content) > 50 else user_message_content
                conversation.save()

            logger.info(f"Generated response for conversation {conversation.id}")

            return Response(
                {
                    'user_message': MessageSerializer(user_message).data,
                    'assistant_message': MessageSerializer(assistant_message).data
                },
                status=status.HTTP_200_OK
            )

        except LLMAPIError as e:
            logger.error(f"LLM API error for conversation {conversation.id}: {str(e)}")
            return Response(
                {'error': 'Failed to generate LLM response. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Unexpected error in generate_response: {str(e)}")
            return Response(
                {'error': 'An unexpected error occurred.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get all messages in a conversation."""
        conversation = self.get_object()
        messages = conversation.message_set.all().order_by('timestamp')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)


class ResponseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    ordering_fields = ['-created_at']

    def get_queryset(self):
        """Return responses submitted by current user."""
        return ResponseModel.objects.filter(submitted_by=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return ResponseSubmitSerializer
        elif self.action == 'retrieve':
            return ResponseDetailSerializer
        return ResponseListSerializer

    def create(self, request, *args, **kwargs):
        """Submit a response for moderation."""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            response = serializer.save()

            # Create moderation queue entry
            from apps.moderation.models import ModerationQueue
            ModerationQueue.objects.create(
                response=response,
                status='pending'
            )

            return Response(
                ResponseDetailSerializer(response).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """Only delete draft responses."""
        response = self.get_object()

        if response.status != 'draft':
            return Response(
                {'error': f'Cannot delete {response.status} response'},
                status=status.HTTP_400_BAD_REQUEST
            )

        response.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
