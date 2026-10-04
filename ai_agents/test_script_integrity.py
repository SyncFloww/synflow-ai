import json
from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from workspaces.models import Workspace, WorkspaceMember
from social.models import Brand, BrandProfile, BrandVoice, BrandKnowledge
from ai_agents.models import AIJob, AIScript
from ai_agents.providers.base import GenerationResult
from ai_agents.services.studio_services import AIScriptService, ScriptGenerationUnavailable


class ScriptIntegrityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='script-owner')
        self.workspace = Workspace.objects.create(name='Scripts', owner=self.user)
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.user, status='ACTIVE')
        self.brand = Brand.objects.create(workspace=self.workspace, name='Bakery')
        BrandProfile.objects.create(brand=self.brand, products_services=['Sourdough'], do_not_say=['Guaranteed weight loss'])
        BrandVoice.objects.create(brand=self.brand, tone='Warm', goal='Local sales')
        BrandKnowledge.objects.create(brand=self.brand, title='Delivery', content='Delivery on Saturdays')
        self.params = {'topic': 'Bread', 'platform': 'instagram'}

    @patch('ai_agents.services.job_service.LLMProviderRegistry.get')
    def test_valid_json_is_saved_with_brand_context(self, get_provider):
        get_provider.return_value.generate_text.return_value = GenerationResult(
            text=json.dumps({'hook': 'Fresh bread?', 'body': 'Try our sourdough.', 'cta': 'Order today.'})
        )
        script = AIScriptService.generate_script(self.workspace, self.user, self.brand, self.params)
        self.assertEqual(script.body, 'Try our sourdough.')
        self.assertEqual(script.versions.count(), 1)
        context = get_provider.return_value.generate_text.call_args.kwargs['system_prompt']
        for value in ('Bakery', 'Sourdough', 'Local sales', 'Delivery on Saturdays', 'Guaranteed weight loss'):
            self.assertIn(value, context)

    @patch('ai_agents.services.job_service.LLMProviderRegistry.get')
    def test_unusable_responses_never_create_scripts(self, get_provider):
        for output in ({}, {'content': 'mock'}, {'hook': 'Hello', 'body': '', 'cta': 'Buy'},
                       {'hook': 'Hello', 'body': 'Bread', 'cta': 'Buy', 'b_roll_suggestions': 'wrong type'}):
            with self.subTest(output=output):
                get_provider.return_value.generate_text.return_value = GenerationResult(structured_data=output)
                with self.assertRaises(ScriptGenerationUnavailable):
                    AIScriptService.generate_script(self.workspace, self.user, self.brand, self.params)
        self.assertEqual(AIScript.objects.count(), 0)
        self.assertEqual(AIJob.objects.filter(status='FAILED').count(), 4)

    @patch('ai_agents.services.job_service.LLMProviderRegistry.get')
    def test_provider_failure_returns_retryable_api_error(self, get_provider):
        get_provider.return_value.generate_text.side_effect = RuntimeError('sensitive provider details')
        client = APIClient()
        client.force_authenticate(self.user)
        response = client.post('/api/ai/scripts/generate/', {**self.params, 'brand': self.brand.id}, format='json')
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('sensitive', str(response.data))
        self.assertFalse(AIScript.objects.exists())

    def test_invalid_brand_is_rejected_before_generation(self):
        client = APIClient()
        client.force_authenticate(self.user)
        response = client.post('/api/ai/scripts/generate/', {**self.params, 'brand': 99999}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(AIJob.objects.exists())
