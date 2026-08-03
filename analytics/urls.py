from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AnalyticsSnapshotViewSet, PostMetricViewSet, DailyAnalyticsViewSet, UnifiedDashboardView, CollectMetricsView

router = DefaultRouter()
router.register('snapshots', AnalyticsSnapshotViewSet, basename='analytics_snapshot')
router.register('post-metrics', PostMetricViewSet, basename='post_metric')
router.register('daily', DailyAnalyticsViewSet, basename='daily_analytics')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', UnifiedDashboardView.as_view(), name='unified_dashboard'),
    path('collect/', CollectMetricsView.as_view(), name='collect_metrics'),
]
