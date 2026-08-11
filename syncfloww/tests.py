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

        workflow_response = client.get('/api/v2/workflows/')
        self.assertEqual(workflow_response.status_code, 200)

        activity_response = client.get('/api/v2/activities/')
        self.assertEqual(activity_response.status_code, 200)

        csrf_token = client.cookies['csrftoken'].value
        write_response = client.post(
            '/api/v2/workflows/',
            data='{}',
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertNotEqual(write_response.status_code, 403)

    def test_admin_login_accepts_csrf_request_from_trusted_web_origin(self):
        client = Client(HTTP_HOST='api.syncfloww.com', enforce_csrf_checks=True)
        login_page = client.get('/admin/login/?next=/')
        csrf_token = login_page.context['csrf_token']

        response = client.post(
            '/admin/login/?next=/',
            data={
                'username': 'unknown-user',
                'password': 'invalid-password',
                'csrfmiddlewaretoken': csrf_token,
            },
            HTTP_ORIGIN='https://www.syncfloww.com',
        )

        self.assertEqual(response.status_code, 200)
