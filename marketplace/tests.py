from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from .models import MarketplaceApp, PromptPack, PluginExtension

class MarketplaceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='marketuser', email='market@example.com', password='Password123!')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_marketplace_app_list_and_toggle(self):
        app = MarketplaceApp.objects.create(name='Slack Connector', description='Connects workspace notifications to Slack', category='connector')
        response = self.client.get('/api/marketplace/apps/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(f'/api/marketplace/apps/{app.id}/toggle-install/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        app.refresh_from_db()
        self.assertTrue(app.is_installed)

    def test_prompt_packs_and_plugins(self):
        pack = PromptPack.objects.create(title='SaaS Viral Hooks', description='100 high converting SaaS hooks')
        plugin = PluginExtension.objects.create(name='SEO Analyzer Plugin', publisher='SyncflowAI')

        response = self.client.get('/api/marketplace/prompt-packs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get('/api/marketplace/plugins/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
