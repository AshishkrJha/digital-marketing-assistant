from django.db import models
from apps.users.models import User


class Project(models.Model):
    """Project model for multi-project support."""
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_projects')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'project'
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} (Owner: {self.owner.email})"


class UserProject(models.Model):
    """User-Project mapping for multi-tenancy."""
    ROLE_CHOICES = (
        ('member', 'Member'),
        ('admin', 'Admin'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_projects')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='members')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_project'
        verbose_name = 'User Project'
        verbose_name_plural = 'User Projects'
        unique_together = ('user', 'project')

    def __str__(self):
        return f"{self.user.email} - {self.project.name} ({self.get_role_display()})"

    def is_admin(self):
        return self.role == 'admin'


class ProjectArtifact(models.Model):
    """Project-related artifact (text file or image) stored directly in the database."""
    ARTIFACT_TYPES = (
        ('text', 'Text File'),
        ('image', 'Image'),
    )

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='artifacts')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_artifacts')
    artifact_type = models.CharField(max_length=10, choices=ARTIFACT_TYPES)
    file_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    size = models.PositiveIntegerField()
    content = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'project_artifact'
        verbose_name = 'Project Artifact'
        verbose_name_plural = 'Project Artifacts'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.file_name} ({self.project.name})"
