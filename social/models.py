from typing import Optional
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from workspaces.models import Workspace

class Brand(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='brands')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_brands')
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True, default='')
    description = models.TextField(blank=True, default='')
    website = models.URLField(blank=True, default='')
    industry = models.CharField(max_length=255, blank=True, default='')
    logo_url = models.CharField(max_length=1000, blank=True, default='')
    voice = models.CharField(max_length=255, blank=True, default='')
    target_audience = models.CharField(max_length=255, blank=True, default='')
    niche = models.CharField(max_length=255, blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('workspace', 'slug')

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            base_slug = slugify(self.name) or "brand"
            slug = base_slug
            counter = 1
            qs = Brand.objects.filter(workspace=self.workspace) if self.workspace else Brand.objects.all()
            while qs.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class BrandProfile(models.Model):
    brand = models.OneToOneField(Brand, on_delete=models.CASCADE, related_name='profile')
    tagline = models.CharField(max_length=255, blank=True, default='')
    mission = models.TextField(blank=True, default='')
    vision = models.TextField(blank=True, default='')
    industry = models.CharField(max_length=255, blank=True, default='')
    target_audience = models.TextField(blank=True, default='')
    brand_voice = models.CharField(max_length=255, blank=True, default='')
    tone = models.CharField(max_length=255, blank=True, default='')
    language = models.CharField(max_length=50, default='en')
    values = models.JSONField(default=list, blank=True)
    products_services = models.JSONField(default=list, blank=True)
    unique_selling_points = models.JSONField(default=list, blank=True)
    do_not_say = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.brand.name}"

class BrandKnowledge(models.Model):
    KNOWLEDGE_TYPES = (
        ('ABOUT', 'About'),
        ('PRODUCT', 'Product'),
        ('SERVICE', 'Service'),
        ('FAQ', 'FAQ'),
        ('POLICY', 'Policy'),
        ('AUDIENCE', 'Audience'),
        ('CAMPAIGN', 'Campaign'),
        ('GUIDELINE', 'Guideline'),
        ('OTHER', 'Other'),
    )
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='knowledge_items')
    title = models.CharField(max_length=255)
    content = models.TextField()
    knowledge_type = models.CharField(max_length=50, choices=KNOWLEDGE_TYPES, default='OTHER')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.knowledge_type}) for {self.brand.name}"


class BrandAsset(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='assets')
    name = models.CharField(max_length=255)
    file_url = models.CharField(max_length=1000)
    asset_type = models.CharField(max_length=50, default='image') # e.g. logo, font, color-palette
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} for {self.brand.name}"

class BrandVoice(models.Model):
    brand = models.OneToOneField(Brand, on_delete=models.CASCADE, related_name='brand_voice')
    tone = models.CharField(max_length=255) # e.g. humorous, corporate, professional
    goal = models.CharField(max_length=255, blank=True, default='')
    keywords = models.JSONField(default=list, blank=True)
    examples = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Voice for {self.brand.name}"

class BrandGuideline(models.Model):
    brand = models.OneToOneField(Brand, on_delete=models.CASCADE, related_name='guideline')
    fonts = models.JSONField(default=list, blank=True)
    colors = models.JSONField(default=list, blank=True)
    mission = models.TextField(blank=True, default='')
    vision = models.TextField(blank=True, default='')
    website = models.URLField(blank=True, default='')
    industry = models.CharField(max_length=255, blank=True, default='')
    keywords = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Guidelines for {self.brand.name}"

class SocialAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_accounts', null=True, blank=True)
    personal_space = models.ForeignKey('users.PersonalSpace', on_delete=models.CASCADE, null=True, blank=True, related_name='social_accounts')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, null=True, blank=True, related_name='social_accounts')
    connected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='connected_social_accounts')
    platform = models.CharField(max_length=50)  # e.g., 'instagram', 'facebook', 'linkedin', 'tiktok', 'x', 'twitter', 'youtube'
    username = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, blank=True, default='')
    profile_image_url = models.CharField(max_length=1000, blank=True, default='')
    account_id = models.CharField(max_length=255, blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        from django.core.exceptions import ValidationError
        if bool(self.personal_space_id) and bool(self.brand_id):
            raise ValidationError("A social account must belong to EITHER a Personal Space OR a Brand, not both.")
        if not self.personal_space_id and not self.brand_id and not self.user_id and not self.connected_by_id:
            raise ValidationError("A social account must be attached to either a Personal Space or a Brand.")

    def save(self, *args, **kwargs):
        from django.core.exceptions import ValidationError

        # Enforce tenancy isolation: cannot belong to both
        if self.personal_space_id and self.brand_id:
            raise ValidationError("A social account cannot belong to both a Personal Space and a Brand.")

        # Auto-resolve ownership if neither is explicitly set but user is provided
        if not self.personal_space_id and not self.brand_id:
            owner_user = self.connected_by or self.user
            if owner_user:
                from users.models import PersonalSpace
                ps, _ = PersonalSpace.objects.get_or_create(user=owner_user)
                self.personal_space = ps
            else:
                raise ValidationError("A social account must be attached to either a Personal Space or a Brand.")

        # Ensure ownership separation
        if self.brand_id:
            self.personal_space = None
        elif self.personal_space_id:
            self.brand = None

        if not self.connected_by_id and self.user_id:
            self.connected_by = self.user
        if not self.user_id and self.connected_by_id:
            self.user = self.connected_by

        super().save(*args, **kwargs)

    @property
    def owner_type(self) -> str:
        return 'brand' if self.brand_id else 'personal_space'

    @property
    def owner_id(self) -> Optional[int]:
        return self.brand_id if self.brand_id else self.personal_space_id

    @property
    def owner_name(self) -> str:
        if self.brand:
            return self.brand.name
        if self.personal_space:
            return self.personal_space.name
        return ''

    def __str__(self):
        owner_str = f"Brand: {self.brand.name}" if self.brand else f"PersonalSpace: {self.personal_space_id}"
        return f"{self.platform} - {self.username} ({owner_str})"

class PlatformCredential(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='platform_credentials')
    platform = models.CharField(max_length=50)
    credential_data = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.platform} Credential for {self.user.username}"

class OAuthToken(models.Model):
    social_account = models.OneToOneField(SocialAccount, on_delete=models.CASCADE, related_name='oauth_token')
    access_token = models.TextField()
    refresh_token = models.TextField(blank=True, default='')
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_expired(self) -> bool:
        if self.expires_at:
            from django.utils import timezone
            return self.expires_at <= timezone.now()
        return False

    def __str__(self):
        return f"OAuth Token for {self.social_account}"
