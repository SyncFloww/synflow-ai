from django.contrib.auth.models import User
from django.test import Client, TestCase


class DashboardAuthenticationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='dashboard-user',
            password='test-password-123',
        )

    def test_dashboard_session_authenticates_api_requests_and_sets_csrf_cookie(self):
        anonymous_client = Client(HTTP_HOST='api.syncfloww.com')
        anonymous_response = anonymous_client.get('/')
        self.assertRedirects(anonymous_response, '/admin/login/?next=/')

        client = Client(HTTP_HOST='api.syncfloww.com', enforce_csrf_checks=True)
        client.force_login(self.user)

        dashboard_response = client.get('/')
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertIn('csrftoken', client.cookies)

        api_response = client.get('/api/v2/campaigns/')
        self.assertEqual(api_response.status_code, 200)

        csrf_token = client.cookies['csrftoken'].value
        write_response = client.post(
            '/api/v2/workflows/',
            data='{}',
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertNotEqual(write_response.status_code, 403)
