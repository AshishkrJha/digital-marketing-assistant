from django.db import models
from apps.users.models import User
from apps.projects.models import Project


class Conversation(models.Model):
    """Conversation session between user and LLM."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=255, blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    langchain_memory_key = models.CharField(max_length=255, blank=True, null=True, help_text="LangChain memory identifier")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'conversation'
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversation #{self.id} - {self.user.email} ({self.project.name})"

    def get_title(self):
        """Get conversation title or first message."""
        if self.title:
            return self.title
        first_message = self.message_set.filter(role='user').first()
        if first_message:
            return first_message.content[:50] + '...' if len(first_message.content) > 50 else first_message.content
        return f"Conversation #{self.id}"


class Message(models.Model):
    """Individual messages in a conversation."""
    ROLE_CHOICES = (
        ('user', 'User'),
        ('assistant', 'Assistant'),
    )

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    tokens_used = models.IntegerField(default=0, help_text="Tokens used for this message (for LLM messages)")
    is_submitted = models.BooleanField(default=False, help_text="Whether this message has been submitted for moderation")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'message'
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['conversation', 'timestamp']),
        ]

    def __str__(self):
        preview = self.content[:50] + '...' if len(self.content) > 50 else self.content
        return f"{self.get_role_display()}: {preview}"


class Response(models.Model):
    """Response submitted by user for moderation."""
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    message = models.OneToOneField(Message, on_delete=models.CASCADE, related_name='response')
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_responses')
    content = models.TextField(help_text="The response content submitted for moderation")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'response'
        verbose_name = 'Response'
        verbose_name_plural = 'Responses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['submitted_by', '-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Response #{self.id} - {self.get_status_display()}"


class ResponseApproval(models.Model):
    """Moderation approval record for a response."""
    DECISION_CHOICES = (
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    response = models.OneToOneField(Response, on_delete=models.CASCADE, related_name='approval')
    moderator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approvals_given')
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES)
    comments = models.TextField(blank=True, null=True, help_text="Moderator comments")
    crm_synced = models.BooleanField(default=False, help_text="Whether response has been synced to CRM")
    crm_sync_timestamp = models.DateTimeField(null=True, blank=True, help_text="When response was synced to CRM")
    approved_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'response_approval'
        verbose_name = 'Response Approval'
        verbose_name_plural = 'Response Approvals'
        ordering = ['-approved_at']

    def __str__(self):
        return f"Approval #{self.id} - {self.decision} by {self.moderator.email if self.moderator else 'Unknown'}"
