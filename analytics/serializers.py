from rest_framework import serializers
from .models import AnalyticsSnapshot, PlatformMetric, PostMetric, DailyAnalytics

class PlatformMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformMetric
        fields = '__all__'

class PostMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostMetric
        fields = '__all__'

class AnalyticsSnapshotSerializer(serializers.ModelSerializer):
    metrics_detail = PlatformMetricSerializer(source='metrics', many=True, read_only=True)

    class Meta:
        model = AnalyticsSnapshot
        fields = ['id', 'brand', 'social_account', 'platform', 'followers_count', 'engagement_rate', 'posts_count', 'views_count', 'metrics_detail', 'timestamp']
        read_only_fields = ['user', 'timestamp']

class DailyAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyAnalytics
        fields = '__all__'
