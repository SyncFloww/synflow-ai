from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Avg, Q
from django.shortcuts import get_object_or_404

from .models import AnalyticsSnapshot, PlatformMetric, PostMetric, DailyAnalytics
from .serializers import AnalyticsSnapshotSerializer, PostMetricSerializer, DailyAnalyticsSerializer
from .services import MetricsCollector
from social.models import SocialAccount
from publishing.models import Post

class AnalyticsSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AnalyticsSnapshotSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return AnalyticsSnapshot.objects.filter(
            Q(user=user) | Q(brand__workspace__members__user=user, brand__workspace__members__status='ACTIVE')
        ).distinct().order_by('-timestamp')

class PostMetricViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PostMetricSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return PostMetric.objects.filter(
            Q(post__user=user) | Q(post__workspace__members__user=user, post__workspace__members__status='ACTIVE')
        ).distinct().order_by('-updated_at')

class DailyAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DailyAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return DailyAnalytics.objects.filter(
            Q(brand__workspace__members__user=user, brand__workspace__members__status='ACTIVE') |
            Q(brand__created_by=user)
        ).distinct().order_by('-date')

class CollectMetricsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        social_account_id = request.data.get('social_account_id')
        post_id = request.data.get('post_id')
        platform = request.data.get('platform')

        if social_account_id:
            account = get_object_or_404(SocialAccount, id=social_account_id)
            snapshot = MetricsCollector.collect_account_snapshot(account)
            return Response(AnalyticsSnapshotSerializer(snapshot).data, status=status.HTTP_201_CREATED)

        if post_id and platform:
            post = get_object_or_404(Post, id=post_id)
            post_metric = MetricsCollector.collect_post_metrics(post, platform)
            return Response(PostMetricSerializer(post_metric).data, status=status.HTTP_201_CREATED)

        return Response({'error': 'social_account_id or (post_id and platform) is required.'}, status=status.HTTP_400_BAD_REQUEST)

class UnifiedDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        brand_id = request.query_params.get('brand_id')
        user = request.user
        
        snapshots = AnalyticsSnapshot.objects.filter(
            Q(user=user) | Q(brand__workspace__members__user=user, brand__workspace__members__status='ACTIVE')
        ).distinct()

        daily = DailyAnalytics.objects.filter(
            Q(brand__workspace__members__user=user, brand__workspace__members__status='ACTIVE') | Q(brand__created_by=user)
        ).distinct()
        
        if brand_id:
            snapshots = snapshots.filter(brand_id=brand_id)
            daily = daily.filter(brand_id=brand_id)

        total_followers = snapshots.values('platform').annotate(latest_followers=Sum('followers_count'))
        sum_followers = sum(item['latest_followers'] or 0 for item in total_followers)

        avg_engagement = snapshots.aggregate(Avg('engagement_rate'))['engagement_rate__avg'] or 0.0

        daily_totals = daily.aggregate(
            total_likes=Sum('likes'),
            total_shares=Sum('shares'),
            total_comments=Sum('comments'),
            total_views=Sum('views')
        )

        return Response({
            'total_followers': sum_followers,
            'average_engagement_rate': round(float(avg_engagement), 2),
            'total_likes': daily_totals['total_likes'] or 0,
            'total_shares': daily_totals['total_shares'] or 0,
            'total_comments': daily_totals['total_comments'] or 0,
            'total_views': daily_totals['total_views'] or 0,
            'by_platform': list(total_followers)
        }, status=status.HTTP_200_OK)
