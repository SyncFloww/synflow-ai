from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from workspaces.models import Workspace
from content.models import Content
from .models import ActivityLog, ErrorLog, JobExecutionLog
from .middleware import ActivityLoggingMiddleware

User = get_user_model()

class ObservabilityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@test.com", password="pwd")
        self.workspace = Workspace.objects.create(name="Test", slug="test", owner=self.user)
        self.factory = RequestFactory()

    def test_activity_logging_middleware(self):
        request = self.factory.post(f'/api/v1/workspaces/{self.workspace.id}/generate/', data="{}", content_type="application/json")
        request.user = self.user
        request.META['REMOTE_ADDR'] = '127.0.0.1'

        middleware = ActivityLoggingMiddleware(get_response=lambda req: type('Response', (), {'status_code': 201})())
        response = middleware(request)
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ActivityLog.objects.count(), 1)
        
        log = ActivityLog.objects.first()
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.workspace, self.workspace)
        self.assertEqual(log.action, f"POST /api/v1/workspaces/{self.workspace.id}/generate/")
        self.assertEqual(log.ip_address, '127.0.0.1')
        self.assertEqual(log.details['status_code'], 201)

    def test_error_log_creation(self):
        log = ErrorLog.objects.create(
            workspace=self.workspace,
            module="test_module",
            error_message="A critical failure occurred",
            context={"job_id": "123"}
        )
        self.assertEqual(ErrorLog.objects.count(), 1)
        self.assertEqual(log.module, "test_module")

    def test_job_execution_log(self):
        log = JobExecutionLog.objects.create(
            job_name="process_publish_job",
            job_id="celery_task_456",
            status="started"
        )
        self.assertEqual(JobExecutionLog.objects.count(), 1)
        self.assertEqual(log.status, "started")
