from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from workspaces.models import Workspace, WorkspaceMember
from social.models import Brand
from media.models import Media
from content.models import Content
from ai_agents.models import AIJob, AIScript, AISocialContent, AIContentProject, CustomVoiceProfile, VoiceConsent
from ai_agents.providers import LLMProviderRegistry, VoiceProviderRegistry, ImageProviderRegistry, VideoProviderRegistry
from ai_agents.services import AIIdeaService, AIScriptService, AISocialContentService, AIImageService, AIVoiceService

class AIMediaStudioTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="creator", email="creator@syncfloww.com", password="password123")
        self.other_user = User.objects.create_user(username="other", email="other@syncfloww.com", password="password123")
        
        self.workspace = Workspace.objects.create(name="Creator Space", owner=self.user)
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.user, role="OWNER", status="ACTIVE")
        
        self.other_workspace = Workspace.objects.create(name="Other Space", owner=self.other_user)
        WorkspaceMember.objects.create(workspace=self.other_workspace, user=self.other_user, role="OWNER", status="ACTIVE")

        self.brand = Brand.objects.create(workspace=self.workspace, name="TechBrand", industry="AI")

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_provider_registries(self):
        llm = LLMProviderRegistry.get('gemini')
        self.assertIsNotNone(llm)
        res = llm.generate_text("Test prompt")
        self.assertTrue(len(res.text) > 0)

        voice_prov = VoiceProviderRegistry.get('murf')
        voices = voice_prov.list_voices()
        self.assertTrue(len(voices) > 0)

    def test_idea_to_script_to_social_workflow(self):
        # 1. Generate Idea Job
        idea_job = AIIdeaService.generate_ideas(self.workspace, self.user, self.brand, {"topic": "AI Studio Launch"})
        self.assertIn(idea_job.status, ['QUEUED', 'PROCESSING', 'COMPLETED'])

        # 2. Generate Script
        script = AIScriptService.generate_script(self.workspace, self.user, self.brand, {"topic": "AI Studio Launch", "platform": "tiktok"})
        self.assertIsNotNone(script.id)
        self.assertTrue(len(script.hook) > 0)
        self.assertEqual(script.versions.count(), 1)

        # 3. Convert Script to Social Content
        social_items = AISocialContentService.convert_script_to_social(self.workspace, self.user, self.brand, script)
        self.assertEqual(len(social_items), 6)
        
        # Verify Content Library save
        saved_contents = Content.objects.filter(workspace=self.workspace)
        self.assertTrue(saved_contents.count() >= 6)

    def test_image_and_video_media_library_integration(self):
        # Generate Image
        media_item = AIImageService.generate_image(self.workspace, self.user, self.brand, {"prompt": "A modern AI workspace"})
        self.assertIsNotNone(media_item.id)
        self.assertEqual(media_item.workspace, self.workspace)
        self.assertEqual(Media.objects.filter(workspace=self.workspace).count(), 1)

        # Generate Voiceover
        voice_res = AIVoiceService.generate_voiceover(self.workspace, self.user, self.brand, {"text": "Hello world", "voice_id": "en-US-natalie"})
        self.assertIn("audio_url", voice_res)
        self.assertIn("word_timings", voice_res)

    def test_tenant_isolation(self):
        # User 1 script
        script1 = AIScriptService.generate_script(self.workspace, self.user, self.brand, {"topic": "Tenant 1 Post"})
        
        # Switch auth to User 2
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get('/api/ai/scripts/')
        self.assertEqual(response.status_code, 200)
        results = response.data.get('results') if isinstance(response.data, dict) else response.data
        script_ids = [s['id'] for s in results]
        self.assertNotIn(script1.id, script_ids)


    def test_voice_consent_recording(self):
        profile = CustomVoiceProfile.objects.create(
            workspace=self.workspace,
            user=self.user,
            name="Creator Voice",
            provider_voice_id="custom_123"
        )
        consent = VoiceConsent.objects.create(
            voice_profile=profile,
            user=self.user,
            workspace=self.workspace,
            consent_statement="I authorize Syncfloww to process my voice.",
            signature_name="Creator User"
        )
        self.assertEqual(consent.voice_profile, profile)
        self.assertEqual(consent.signature_name, "Creator User")

    def test_ai_architecture_phase1(self):
        # 1. Test Provider Registry for new providers
        hf_prov = LLMProviderRegistry.get('huggingface')
        self.assertIsNotNone(hf_prov)
        self.assertEqual(hf_prov.provider_name, "huggingface")

        litellm_prov = LLMProviderRegistry.get('litellm')
        self.assertIsNotNone(litellm_prov)
        self.assertEqual(litellm_prov.provider_name, "litellm")

        ollama_prov = LLMProviderRegistry.get('ollama')
        self.assertIsNotNone(ollama_prov)
        self.assertEqual(ollama_prov.provider_name, "ollama")

        # 2. Test AIService execution and automatic AIUsageRecord creation
        from ai_agents.services import AIService, PromptManager, ModelRouter, OutputParser
        from ai_agents.models import AIUsageRecord

        ai_service = AIService()
        
        # Test Hugging Face provider via AIService
        result, usage = ai_service.generate_content(
            prompt="Write a short motivational line for tech founders.",
            user=self.user,
            workspace=self.workspace,
            brand=self.brand,
            task_type="caption",
            platform="linkedin",
            provider="huggingface"
        )

        self.assertTrue(len(result.text) > 0)
        self.assertIsNotNone(usage)
        self.assertEqual(usage.workspace, self.workspace)
        self.assertEqual(usage.provider, "huggingface")
        self.assertEqual(AIUsageRecord.objects.filter(workspace=self.workspace).count(), 1)

        # Test LiteLLM provider via AIService
        res_lite, usage_lite = ai_service.generate_content(
            prompt="Analyze comment intent.",
            user=self.user,
            workspace=self.workspace,
            task_type="sentiment",
            provider="litellm"
        )
        self.assertTrue(len(res_lite.text) > 0)
        self.assertIsNotNone(usage_lite)
        self.assertEqual(usage_lite.provider, "litellm")

        # Test PromptManager
        pm = PromptManager()
        sys_prompt = pm.build_system_prompt(task_type="script", platform="tiktok", brand=self.brand)
        self.assertIn("TIKTOK", sys_prompt.upper())
        self.assertIn("TechBrand", sys_prompt)

        # Test ModelRouter
        mr = ModelRouter()
        prov, model = mr.resolve_target(task_type="sentiment")
        self.assertEqual(prov, "gemini")

        prov_hf, model_hf = mr.resolve_target(provider="huggingface")
        self.assertEqual(prov_hf, "huggingface")
        self.assertIn("Llama", model_hf)
