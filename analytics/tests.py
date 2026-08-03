from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from workspaces.models import Workspace, WorkspaceMember
from social.models import Brand, SocialAccount
from publishing.models import Post
from analytics.models import AnalyticsSnapshot, PostMetric
from analytics.services import MetricsCollector, EventBus, MockAnalyticsProvider

class AnalyticsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='analyticsuser', email='a@example.com', password='Password123!')
        self.client.force_authenticate(user=self.user)
        self.workspace = Workspace.objects.create(name='Analytics WS', owner=self.user)
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.user, role='OWNER', status='ACTIVE')
        self.brand = Brand.objects.create(name='Analytics Brand', workspace=self.workspace, created_by=self.user)
        self.social_account = SocialAccount.objects.create(
            user=self.user,
            brand=self.brand,
            platform='instagram',
            account_name='test_ig',
            account_id='ig_123',
            is_active=True
        )
        self.post = Post.objects.create(
            user=self.user,
            brand=self.brand,
            workspace=self.workspace,
            caption='Analytics Post Test'
        )

    def test_collect_account_snapshot(self):
        snapshot = MetricsCollector.collect_account_snapshot(self.social_account)
        self.assertEqual(snapshot.platform, 'instagram')
        self.assertGreater(snapshot.followers_count, 0)

    def test_collect_post_metrics(self):
        post_metric = MetricsCollector.collect_post_metrics(self.post, 'instagram')
        self.assertEqual(post_metric.platform, 'instagram')
        self.assertGreater(post_metric.reach, 0)

    def test_collect_metrics_api(self):
        url = '/api/analytics/collect/'
        response = self.client.post(url, {'social_account_id': self.social_account.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['platform'], 'instagram')

    def test_unified_dashboard_api(self):
        MetricsCollector.collect_account_snapshot(self.social_account)
        url = '/api/analytics/dashboard/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_followers', response.data)
