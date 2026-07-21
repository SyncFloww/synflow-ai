from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework.test import APITestCase
from workspaces.models import Workspace
from accounts.models import User
from .models import AIModel, PromptTemplate, ContentGeneration, GenerationHistory
from .services import AIService

class AIContentAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@example.com", password="StrongPass123!", first_name="Test", last_name="User")
        self.workspace = Workspace.objects.create(name="Test Workspace", slug="test-workspace", owner=self.user)
        self.ai_model = AIModel.objects.create(name="MockGPT", provider_string="mock/gpt-4o", is_active=True)
        self.client.force_authenticate(user=self.user)

    @patch('content_ai.services.completion')
    def test_generate_text_success(self, mock_completion):
        # Mock litellm completion response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Here is a great caption!"
        mock_response.usage.total_tokens = 50
        mock_response.model_dump.return_value = {"id": "chatcmpl-123"}
        mock_completion.return_value = mock_response

        url = reverse('ai-generate', kwargs={'workspace_id': self.workspace.id})
        data = {
            "type": "caption",
            "topic": "Summer Sale",
            "tone": "excited",
            "platform": "instagram"
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["generated_text"], "Here is a great caption!")
        
        gen = ContentGeneration.objects.get(id=response.data["id"])
        self.assertEqual(gen.topic, "Summer Sale")
        self.assertEqual(gen.generated_text, "Here is a great caption!")
        
        history = GenerationHistory.objects.get(generation=gen)
        self.assertEqual(history.tokens_used, 50)
        self.assertIn("Summer Sale", history.full_prompt)

    @patch('content_ai.services.completion')
    def test_provider_failure_logs_error(self, mock_completion):
        mock_completion.side_effect = Exception("Provider timeout")
        
        url = reverse('ai-generate', kwargs={'workspace_id': self.workspace.id})
        data = {"type": "caption", "topic": "Failure Test"}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.data["error"], "AI Provider error")
        
        # Generation should exist without generated text
        gen = ContentGeneration.objects.get(topic="Failure Test")
        self.assertEqual(gen.generated_text, "")
        
        # History should capture the error
        history = GenerationHistory.objects.get(generation=gen)
        self.assertIn("error", history.provider_response)
        self.assertEqual(history.provider_response["error"], "Provider timeout")

    def test_prompt_template_usage(self):
        template = PromptTemplate.objects.create(
            workspace=self.workspace,
            name="caption",
            system_prompt="You are a funny bot.",
            user_prompt_template="Make a joke about {topic} for {platform}"
        )
        
        with patch('content_ai.services.completion') as mock_completion:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Joke!"
            mock_response.model_dump.return_value = {"type": "joke"}
            mock_response.usage.total_tokens = 10
            mock_completion.return_value = mock_response
            
            url = reverse('ai-generate', kwargs={'workspace_id': self.workspace.id})
            data = {"type": "caption", "topic": "cats", "platform": "x"}
            self.client.post(url, data, format='json')
            
            gen = ContentGeneration.objects.get(topic="cats")
            self.assertEqual(gen.template_used, template)
            
            history = GenerationHistory.objects.get(generation=gen)
            self.assertIn("You are a funny bot.", history.full_prompt)
            self.assertIn("Make a joke about cats for x", history.full_prompt)
