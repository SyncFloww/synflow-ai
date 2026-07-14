import uuid
import hashlib
import secrets
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
)

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    email = models.EmailField(
        unique=True,
        db_index=True,
    )

    first_name = models.CharField(
        max_length=100,
    )

    last_name = models.CharField(
        max_length=100,
    )

    referral_code = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
    )

    referred_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="referrals",
    )

    is_verified = models.BooleanField(
        default=False,
    )

    is_active = models.BooleanField(
        default=True,
    )

    is_staff = models.BooleanField(
        default=False,
    )

    date_joined = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        ordering = ["-date_joined"]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ImageField(upload_to="avatars/", blank=True)
    timezone = models.CharField(max_length=64, default="UTC")
    language = models.CharField(max_length=10, default="en")
    theme = models.CharField(max_length=16, default="system")
    updated_at = models.DateTimeField(auto_now=True)


class ExpiringToken(models.Model):
    """Stores only a hash; the raw one-time token is never persisted."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    @classmethod
    def issue(cls, user, lifetime=timedelta(hours=24)):
        raw_token = secrets.token_urlsafe(32)
        instance = cls.objects.create(
            user=user,
            token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
            expires_at=timezone.now() + lifetime,
        )
        return instance, raw_token

    @classmethod
    def consume(cls, raw_token):
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        instance = cls.objects.filter(token_hash=token_hash, used_at__isnull=True, expires_at__gt=timezone.now()).first()
        if not instance:
            return None
        instance.used_at = timezone.now()
        instance.save(update_fields=["used_at"])
        return instance


class EmailVerification(ExpiringToken):
    pass


class PasswordReset(ExpiringToken):
    pass


class UserDevice(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="devices")
    name = models.CharField(max_length=128, blank=True)
    user_agent = models.TextField(blank=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
