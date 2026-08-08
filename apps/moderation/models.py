from django.db import models
from apps.users.models import User
from apps.conversations.models import Response


class ModerationQueue(models.Model):
    """Queue for responses awaiting moderation."""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processed', 'Processed'),
    )

    response = models.OneToOneField(Response, on_delete=models.CASCADE, related_name='moderation_queue')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_moderations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'moderation_queue'
        verbose_name = 'Moderation Queue'
        verbose_name_plural = 'Moderation Queues'
        ordering = ['status', '-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"Queue #{self.id} - Response #{self.response.id} ({self.get_status_display()})"


class ModerationLog(models.Model):
    """Audit log for moderation actions."""
    ACTION_CHOICES = (
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('reassigned', 'Reassigned'),
    )

    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name='moderation_logs')
    moderator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='moderation_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    notes = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'moderation_log'
        verbose_name = 'Moderation Log'
        verbose_name_plural = 'Moderation Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['moderator', '-timestamp']),
            models.Index(fields=['response']),
        ]

    def __str__(self):
        return f"Log #{self.id} - {self.action} by {self.moderator.email if self.moderator else 'Unknown'}"
