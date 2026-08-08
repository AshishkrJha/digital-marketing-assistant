from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from apps.moderation.models import ModerationQueue, ModerationLog
from apps.conversations.models import Response as ResponseModel, ResponseApproval
from apps.moderation.serializers import (
    ModerationQueueSerializer,
    ApprovalDecisionSerializer,
    ModerationHistorySerializer,
)
from core.permissions import IsModeratorOrAdmin
from core.exceptions import InvalidModerationAction
from core.utils import log_moderation_action, create_crm_payload
import logging

logger = logging.getLogger('moderation')


class ModerationQueueViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsModeratorOrAdmin]
    serializer_class = ModerationQueueSerializer
    ordering_fields = ['-created_at']

    def get_queryset(self):
        """Return pending responses for moderation."""
        return ModerationQueue.objects.select_related(
            'response__submitted_by',
            'response__message__conversation__project'
        ).filter(status='pending')

    def list(self, request, *args, **kwargs):
        """List all pending responses awaiting moderation."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        """Get details of a specific pending response."""
        queue_entry = self.get_object()
        serializer = self.get_serializer(queue_entry)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a response and sync to CRM."""
        queue_entry = self.get_object()
        response_obj = queue_entry.response

        serializer = ApprovalDecisionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if serializer.validated_data['decision'] != 'approved':
            return Response(
                {'error': 'Use reject action for rejecting responses'},
                status=status.HTTP_400_BAD_REQUEST
            )

        comments = serializer.validated_data.get('comments', '')

        try:
            # Create approval record
            approval = ResponseApproval.objects.create(
                response=response_obj,
                moderator=request.user,
                decision='approved',
                comments=comments
            )

            # Update response status
            response_obj.status = 'approved'
            response_obj.save()

            # Update moderation queue
            queue_entry.status = 'processed'
            queue_entry.save()

            # Log moderation action
            log_moderation_action(response_obj, request.user, 'approved', comments)

            # Sync to CRM
            try:
                from apps.integrations.crm_service import sync_to_crm
                from django.conf import settings

                payload = create_crm_payload(response_obj, request.user)
                webhook_url = settings.CRM_WEBHOOK_URL

                crm_success = sync_to_crm(response_obj, webhook_url, payload)

                if crm_success:
                    approval.crm_synced = True
                    approval.crm_sync_timestamp = timezone.now()
                    approval.save()

                    logger.info(f"Response {response_obj.id} approved and synced to CRM")
                else:
                    logger.warning(f"Response {response_obj.id} approved but CRM sync failed")

            except Exception as e:
                logger.error(f"CRM sync error for response {response_obj.id}: {str(e)}")
                # Don't fail the approval, but mark as not synced

            return Response(
                {
                    'message': 'Response approved successfully',
                    'crm_synced': approval.crm_synced
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error approving response {response_obj.id}: {str(e)}")
            return Response(
                {'error': 'Failed to approve response'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a response with comments."""
        queue_entry = self.get_object()
        response_obj = queue_entry.response

        serializer = ApprovalDecisionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if serializer.validated_data['decision'] != 'rejected':
            return Response(
                {'error': 'Use approve action for approving responses'},
                status=status.HTTP_400_BAD_REQUEST
            )

        comments = serializer.validated_data.get('comments', '')

        try:
            # Create approval record
            approval = ResponseApproval.objects.create(
                response=response_obj,
                moderator=request.user,
                decision='rejected',
                comments=comments
            )

            # Update response status
            response_obj.status = 'rejected'
            response_obj.save()

            # Update moderation queue
            queue_entry.status = 'processed'
            queue_entry.save()

            # Log moderation action
            log_moderation_action(response_obj, request.user, 'rejected', comments)

            logger.info(f"Response {response_obj.id} rejected by {request.user.email}")

            return Response(
                {
                    'message': 'Response rejected successfully',
                    'comments': comments
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error rejecting response {response_obj.id}: {str(e)}")
            return Response(
                {'error': 'Failed to reject response'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ModerationHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """View-only access to moderation history (audit log)."""
    permission_classes = [IsAuthenticated, IsModeratorOrAdmin]
    serializer_class = ModerationHistorySerializer
    queryset = ModerationLog.objects.select_related(
        'moderator', 'response__submitted_by'
    ).order_by('-timestamp')
    ordering_fields = ['-timestamp', 'action']

    def list(self, request, *args, **kwargs):
        """List all moderation actions (admin only)."""
        if request.user.role != 'admin':
            return Response(
                {'error': 'Only admins can view full moderation history'},
                status=status.HTTP_403_FORBIDDEN
            )

        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })
