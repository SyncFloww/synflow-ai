from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.test import APITestCase

from workspaces.models import Workspace, WorkspaceMember
from social.models import Brand
from publishing.models import Post, PostPlatform, PublishJob, PublishLog
from publishing.services import PublishingService

class PublishingServiceTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='pubuser', email='pub@example.com', password='Password123!')
        self.workspace = Workspace.objects.create(name='Pub WS', owner=self.user)
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.user, role='OWNER', status='ACTIVE')
        self.brand = Brand.objects.create(name='Pub Brand', workspace=self.workspace, created_by=self.user)

    def test_create_and_pipeline_transitions(self):
        post = PublishingService.create_post(
            user=self.user,
            brand=self.brand,
            caption="Hello world",
            platforms=['instagram', 'linkedin']
        )
        self.assertEqual(post.status, 'draft')

        PublishingService.submit_for_review(post)
        self.assertEqual(post.status, 'review')

        PublishingService.approve_post(post)
        self.assertEqual(post.status, 'approved')

        future_time = timezone.now() + timedelta(days=1)
        PublishingService.schedule_post(post, future_time)
        self.assertEqual(post.status, 'scheduled')
        self.assertTrue(PublishJob.objects.filter(post=post, status='pending').exists())

    def test_publish_now_execution(self):
        post = PublishingService.create_post(
            user=self.user,
            brand=self.brand,
            caption="Publish immediately",
            platforms=['instagram', 'x']
        )

        res = PublishingService.publish_now(post)
        self.assertEqual(res['status'], 'published')
        self.assertEqual(post.status, 'published')
        self.assertTrue(PublishLog.objects.filter(job__post=post).exists())

    def test_cancel_post(self):
        future_time = timezone.now() + timedelta(days=2)
        post = PublishingService.create_post(
            user=self.user,
            brand=self.brand,
            caption="To cancel",
            scheduled_at=future_time
        )
        self.assertEqual(post.status, 'scheduled')

        PublishingService.cancel_post(post)
        self.assertEqual(post.status, 'archived')
        self.assertTrue(PublishJob.objects.filter(post=post, status='cancelled').exists())


class PublishingAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='apiuser', email='api@example.com', password='Password123!')
        self.client.force_authenticate(user=self.user)
        self.workspace = Workspace.objects.create(name='API WS', owner=self.user)
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.user, role='OWNER', status='ACTIVE')
        self.brand = Brand.objects.create(name='API Brand', workspace=self.workspace, created_by=self.user)

    def test_post_crud(self):
        url = '/api/publishing/posts/'
        response = self.client.post(url, {
            'caption': 'API Test Post',
            'brand': self.brand.id,
            'workspace': self.workspace.id
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post_id = response.data['id']

        # Publish Now
        pub_url = f'/api/publishing/posts/{post_id}/publish-now/'
        response = self.client.post(pub_url, {'platforms': ['instagram', 'linkedin']}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'published')

    def test_schedule_and_reschedule_api(self):
        url = '/api/publishing/posts/'
        response = self.client.post(url, {'caption': 'Schedule me'}, format='json')
        post_id = response.data['id']

        sched_url = f'/api/publishing/posts/{post_id}/schedule/'
        future = (timezone.now() + timedelta(hours=5)).isoformat()
        res = self.client.post(sched_url, {'scheduled_at': future}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['status'], 'scheduled')

        resched_url = f'/api/publishing/posts/{post_id}/reschedule/'
        new_future = (timezone.now() + timedelta(hours=10)).isoformat()
        res = self.client.post(resched_url, {'scheduled_at': new_future}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['status'], 'scheduled')
