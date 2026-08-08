from django.db import models


class GeminiLog(models.Model):
    """Log for Gemini API calls and token usage."""
    conversation = models.ForeignKey('conversations.Conversation', on_delete=models.CASCADE, related_name='gemini_logs')
    request_tokens = models.IntegerField(default=0)
    response_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    model = models.CharField(max_length=100, default='gemini-pro')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'gemini_log'
        verbose_name = 'Gemini Log'
        verbose_name_plural = 'Gemini Logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"Gemini Log #{self.id} - {self.model} ({self.total_tokens} tokens)"


class CRMLog(models.Model):
    """Log for CRM webhook integration."""
    STATUS_CHOICES = (
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    )

    response = models.OneToOneField('conversations.Response', on_delete=models.CASCADE, related_name='crm_log')
    webhook_url = models.URLField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    response_code = models.IntegerField(null=True, blank=True)
    attempt_count = models.IntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'crm_log'
        verbose_name = 'CRM Log'
        verbose_name_plural = 'CRM Logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"CRM Log #{self.id} - {self.response.id} ({self.get_status_display()})"
