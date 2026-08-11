from rest_framework import serializers
from .models import Brand, BrandProfile, BrandKnowledge, BrandAsset, BrandVoice, BrandGuideline, SocialAccount, PlatformCredential, OAuthToken

class BrandProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandProfile
        fields = '__all__'
        read_only_fields = ['id', 'brand', 'created_at', 'updated_at']

class BrandKnowledgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandKnowledge
        fields = '__all__'
        read_only_fields = ['id', 'brand', 'created_at', 'updated_at']

class BrandAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandAsset
        fields = '__all__'

class BrandVoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandVoice
        fields = '__all__'

class BrandGuidelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandGuideline
        fields = '__all__'

class BrandSerializer(serializers.ModelSerializer):
    workspace_name = serializers.ReadOnlyField(source='workspace.name')
    created_by_username = serializers.ReadOnlyField(source='created_by.username')
    profile_detail = BrandProfileSerializer(source='profile', read_only=True)
    voice_detail = BrandVoiceSerializer(source='brand_voice', read_only=True)
    guidelines_detail = BrandGuidelineSerializer(source='guideline', read_only=True)

    class Meta:
        model = Brand
        fields = [
            'id', 'workspace', 'workspace_name', 'created_by', 'created_by_username',
            'name', 'slug', 'description', 'website', 'industry', 'logo_url', 'voice',
            'target_audience', 'niche', 'is_active', 'profile_detail', 'voice_detail',
            'guidelines_detail', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'workspace', 'created_by', 'created_at', 'updated_at']


class OAuthTokenSerializer(serializers.ModelSerializer):
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = OAuthToken
        fields = ['id', 'social_account', 'expires_at', 'is_expired', 'created_at']

    def get_is_expired(self, obj):
        if obj.expires_at:
            from django.utils import timezone
            return obj.expires_at <= timezone.now()
        return False

class SocialAccountSerializer(serializers.ModelSerializer):
    oauth_token_detail = OAuthTokenSerializer(source='oauth_token', read_only=True)
    connected_by_username = serializers.ReadOnlyField(source='connected_by.username')
    brand_name = serializers.ReadOnlyField(source='brand.name')
    owner_type = serializers.ReadOnlyField()
    owner_id = serializers.ReadOnlyField()
    owner_name = serializers.ReadOnlyField()

    class Meta:
        model = SocialAccount
        fields = [
            'id', 'personal_space', 'brand', 'brand_name', 'owner_type', 'owner_id', 'owner_name',
            'connected_by', 'connected_by_username', 'platform', 'username', 'display_name',
            'profile_image_url', 'account_id', 'is_active', 'oauth_token_detail', 'created_at'
        ]
        read_only_fields = ['id', 'connected_by', 'created_at']

class PlatformCredentialSerializer(serializers.ModelSerializer):
    has_credentials = serializers.SerializerMethodField()

    class Meta:
        model = PlatformCredential
        fields = ['id', 'platform', 'is_active', 'has_credentials', 'created_at']

    def get_has_credentials(self, obj):
        return bool(obj.credential_data)
