from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

class Workspace(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_workspaces')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_workspaces')
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True, default='')
    description = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            base_slug = slugify(self.name) or "workspace"
            slug = base_slug
            counter = 1
            while Workspace.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        if not self.created_by_id and self.owner_id:
            self.created_by = self.owner
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class WorkspaceMember(models.Model):
    ROLE_CHOICES = (
        ('OWNER', 'Owner'),
        ('ADMIN', 'Admin'),
        ('MANAGER', 'Manager'),
        ('MEMBER', 'Member'),
        # Backward compatibility choices
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('editor', 'Editor'),
        ('viewer', 'Viewer'),
    )
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('INVITED', 'Invited'),
        ('SUSPENDED', 'Suspended'),
        ('REMOVED', 'Removed'),
    )
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workspace_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='MEMBER')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('workspace', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.role} ({self.status}) in {self.workspace.name}"

class Invitation(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='invitations')
    email = models.EmailField()
    role = models.CharField(max_length=20, default='MEMBER')
    token = models.CharField(max_length=100, unique=True)
    is_accepted = models.BooleanField(default=False)
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    @property
    def invited_email(self):
        return self.email

    @property
    def created_by(self):
        return self.invited_by

    def __str__(self):
        return f"Invite to {self.email} for {self.workspace.name}"


class WorkspaceSetting(models.Model):
    workspace = models.OneToOneField(Workspace, on_delete=models.CASCADE, related_name='setting')
    language = models.CharField(max_length=10, default='en')
    timezone = models.CharField(max_length=100, default='UTC')
    theme = models.CharField(max_length=50, default='light')
    ai_defaults = models.JSONField(default=dict, blank=True)
    notification_preferences = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Settings for {self.workspace.name}"
