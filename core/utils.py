import logging
from core.exceptions import InvalidProjectAccess

logger = logging.getLogger(__name__)


def get_user_projects(user):
    """Get all projects accessible to a user."""
    from apps.projects.models import UserProject, Project

    owned_projects = Project.objects.filter(owner=user)
    member_projects = Project.objects.filter(
        userproject__user=user
    ).exclude(owner=user)

    return owned_projects | member_projects


def get_project_or_forbidden(project_id, user):
    """
    Get project and verify user has access.
    Raises InvalidProjectAccess if user doesn't have access.
    """
    from apps.projects.models import Project, UserProject

    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        raise InvalidProjectAccess(f"Project {project_id} not found")

    # Check if user is owner
    if project.owner == user:
        return project

    # Check if user is member
    if UserProject.objects.filter(user=user, project=project).exists():
        return project

    raise InvalidProjectAccess(f"User doesn't have access to project {project_id}")


def log_moderation_action(response, moderator, action, notes=''):
    """Log a moderation action for audit trail."""
    from apps.moderation.models import ModerationLog

    ModerationLog.objects.create(
        response=response,
        moderator=moderator,
        action=action,
        notes=notes
    )

    logger.info(
        f"Moderation action: {action} | Response: {response.id} | Moderator: {moderator.id}"
    )


def create_crm_payload(response, moderator):
    """
    Create CRM webhook payload from approved response.
    Standard format: {user_id, project_id, response_content, timestamp, moderator_id}
    """
    from django.utils import timezone

    return {
        'user_id': str(response.submitted_by.id),
        'user_email': response.submitted_by.email,
        'project_id': str(response.message.conversation.project.id),
        'project_name': response.message.conversation.project.name,
        'response_content': response.content,
        'response_id': str(response.id),
        'timestamp': timezone.now().isoformat(),
        'moderator_id': str(moderator.id),
        'moderator_email': moderator.email,
        'conversation_id': str(response.message.conversation.id),
        'status': 'approved'
    }


def get_conversation_summary(conversation):
    """Get a summary of conversation for display."""
    messages = conversation.message_set.all().order_by('timestamp')

    if not messages.exists():
        return "No messages"

    last_message = messages.last()
    message_count = messages.count()

    return {
        'message_count': message_count,
        'last_message': last_message.content[:100] + '...' if len(last_message.content) > 100 else last_message.content,
        'last_message_time': last_message.timestamp,
    }
