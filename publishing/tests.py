from django.test import TestCase
from django.utils import timezone
from workspaces.models import Workspace
from accounts.models import User
from content.models import Content
from social_accounts.models import SocialAccount, Platform, ConnectionStatus
from .models import Post, PostPlatform, Schedule, PublishJob, PublishResult
from .services import MockSocialProviderService
from .tasks import process_publish_job, process_schedule

class PublishingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@example.com", password="StrongPass123!")
        self.workspace = Workspace.objects.create(name="Test Workspace", slug="test-workspace", owner=self.user)
        self.content = Content.objects.create(workspace=self.workspace, author=self.user, text_content="Awesome post!")
        
        self.social_account = SocialAccount.objects.create(
            workspace=self.workspace, platform=Platform.MOCK, platform_account_id="123", status=ConnectionStatus.CONNECTED
        )
        
        self.post = Post.objects.create(workspace=self.workspace, content=self.content, created_by=self.user)
        self.post_platform = PostPlatform.objects.create(post=self.post, social_account=self.social_account)

    def test_mock_provider_success(self):
        job = PublishJob.objects.create(post_platform=self.post_platform)
        MockSocialProviderService.publish_post(job)
        
        job.refresh_from_db()
        self.assertEqual(job.status, PublishJob.Status.SUCCESS)
        self.assertTrue(hasattr(job, 'result'))
        self.assertTrue(job.result.success)
        self.assertEqual(job.result.platform_post_url, f"https://mock.com/mock_post/{job.id}")

    def test_mock_provider_failure(self):
        # Trigger the simulated failure
        self.content.text_content = "This post will fail."
        self.content.save()
        
        job = PublishJob.objects.create(post_platform=self.post_platform)
        MockSocialProviderService.publish_post(job)
        
        job.refresh_from_db()
        self.assertEqual(job.status, PublishJob.Status.FAILED)
        self.assertTrue(hasattr(job, 'result'))
        self.assertFalse(job.result.success)
        self.assertEqual(job.result.error_message, "Simulated network or API error")

    def test_process_schedule_task(self):
        schedule = Schedule.objects.create(post=self.post, scheduled_time=timezone.now())
        
        # Run task synchronously
        process_schedule(schedule.id)
        
        schedule.refresh_from_db()
        self.assertFalse(schedule.is_active)
        
        # A PublishJob should be created and processed
        jobs = PublishJob.objects.filter(post_platform__post=self.post)
        self.assertEqual(jobs.count(), 1)
        self.assertEqual(jobs.first().status, PublishJob.Status.SUCCESS)
