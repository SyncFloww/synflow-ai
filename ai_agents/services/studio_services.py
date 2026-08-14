import logging
from typing import Dict, Any, List, Optional
from django.utils import timezone
from media.models import Media
from content.models import Content, ContentVersion
from ai_agents.models import (
    AIJob,
    AIContentProject,
    AIScript,
    AIScriptVersion,
    AISocialContent,
    AudioProject,
    CustomVoiceProfile,
    VoiceConsent,
    AICaption,
    AIUsageRecord,
    GeneratedContent,
    AIModel
)
from ai_agents.services.job_service import AIJobService
from ai_agents.providers import LLMProviderRegistry

logger = logging.getLogger(__name__)

class ContentGeneratorService:
    @staticmethod
    def generate_content(
        user,
        prompt: str,
        brand=None,
        platform: str = 'instagram',
        content_type: str = 'post',
        model_alias: str = 'gemini-3.5-flash'
    ) -> Dict[str, Any]:
        llm = LLMProviderRegistry.get('gemini')
        context_str = f"\nBrand Name: {brand.name}\nIndustry: {getattr(brand, 'industry', 'General')}" if brand else ""
        full_prompt = f"Write a high-converting social media {content_type} for {platform}.\nTopic/Prompt: {prompt}\n{context_str}\nKeep it engaging with hashtags and call to action."
        
        res = llm.generate_text(prompt=full_prompt)
        generated_text = res.text

        workspace = brand.workspace if brand else None
        content = Content.objects.create(
            user=user,
            workspace=workspace,
            brand=brand,
            title=f"Campaign Content: {prompt[:30]}",
            text_content=generated_text,
            platform=platform
        )

        ContentVersion.objects.create(
            content=content,
            version_number=1,
            text_content=content.text_content
        )

        ai_model, _ = AIModel.objects.get_or_create(
            model_id=model_alias,
            defaults={'name': model_alias, 'provider': 'gemini'}
        )

        gen_record = GeneratedContent.objects.create(
            user=user,
            brand=brand,
            prompt_used=prompt,
            content_text=generated_text,
            platform=platform,
            model_used=ai_model
        )

        return {
            'content_id': content.id,
            'generated_content_id': gen_record.id,
            'generated_text': generated_text,
            'platform': platform
        }


class AIIdeaService:
    @staticmethod
    def generate_ideas(workspace, user, brand, params: Dict[str, Any]) -> AIJob:
        job = AIJobService.create_job(
            workspace=workspace,
            user=user,
            brand=brand,
            job_type='idea',
            input_data=params,
            provider=params.get('provider', 'gemini')
        )
        AIJobService.dispatch_job_async(str(job.id))
        return job


class AIScriptService:
    @staticmethod
    def generate_script(workspace, user, brand, params: Dict[str, Any], project=None) -> AIScript:
        job = AIJobService.create_job(
            workspace=workspace,
            user=user,
            brand=brand,
            job_type='script',
            input_data=params,
            provider=params.get('provider', 'gemini')
        )
        job = AIJobService.execute_job_sync(str(job.id))
        out = job.output_data

        script = AIScript.objects.create(
            project=project,
            workspace=workspace,
            user=user,
            brand=brand,
            title=params.get('topic', 'AI Generated Script'),
            topic=params.get('topic', ''),
            platform=params.get('platform', 'tiktok'),
            target_audience=params.get('audience', ''),
            tone=params.get('tone', ''),
            duration_seconds=params.get('duration', 30),
            hook=out.get('hook') or f"Stop scrolling! Here is what you need to know about {params.get('topic', 'this topic')}:",
            body=out.get('body') or f"First, focus on high quality content. Second, stay consistent.",
            transitions=out.get('transitions', 'Fast cut'),
            cta=out.get('cta') or "Follow for more strategies!",
            visual_directions=out.get('visual_directions', 'Creator on camera with captions.'),
            b_roll_suggestions=out.get('b_roll_suggestions', []),
            voiceover_text=out.get('voiceover_text') or out.get('body', ''),
            onscreen_text=out.get('onscreen_text', '')
        )


        AIScriptVersion.objects.create(
            script=script,
            version_number=1,
            hook=script.hook,
            body=script.body,
            cta=script.cta,
            voiceover_text=script.voiceover_text,
            visual_directions=script.visual_directions,
            change_summary='Initial generation'
        )

        return script

    @staticmethod
    def create_version(script: AIScript, change_summary: str = "Script update") -> AIScriptVersion:
        latest_ver = script.versions.first()
        next_ver_num = (latest_ver.version_number + 1) if latest_ver else 1
        return AIScriptVersion.objects.create(
            script=script,
            version_number=next_ver_num,
            hook=script.hook,
            body=script.body,
            cta=script.cta,
            voiceover_text=script.voiceover_text,
            visual_directions=script.visual_directions,
            change_summary=change_summary
        )


class AISocialContentService:
    @staticmethod
    def convert_script_to_social(workspace, user, brand, script: AIScript) -> List[AISocialContent]:
        input_data = {
            "topic": script.topic,
            "voiceover_text": script.voiceover_text or script.body,
            "cta": script.cta
        }
        job = AIJobService.create_job(
            workspace=workspace,
            user=user,
            brand=brand,
            job_type='social_content',
            input_data=input_data
        )
        job = AIJobService.execute_job_sync(str(job.id))
        outputs = job.output_data

        social_items = []
        platforms = ["instagram", "linkedin", "x", "facebook", "tiktok", "youtube"]
        for p in platforms:
            caption_text = outputs.get(p, f"Derived post for {p}: {script.title}")
            saved_content = Content.objects.create(
                user=user,
                workspace=workspace,
                brand=brand,
                title=f"{script.title} ({p.capitalize()})",
                text_content=caption_text,
                platform=p,
                tags=["AI Studio", script.platform]
            )
            ContentVersion.objects.create(
                content=saved_content,
                text_content=caption_text,
                version_number=1
            )
            
            sc = AISocialContent.objects.create(
                script=script,
                workspace=workspace,
                user=user,
                brand=brand,
                platform=p,
                content_type='caption' if p in ['instagram', 'tiktok'] else 'post',
                caption=caption_text,
                hashtags=["#Syncfloww", "#AIGenerated"],
                call_to_action=script.cta,
                saved_content_id=saved_content.id
            )
            social_items.append(sc)
        return social_items


class AIImageService:
    @staticmethod
    def generate_image(workspace, user, brand, params: Dict[str, Any]) -> Media:
        job = AIJobService.create_job(
            workspace=workspace,
            user=user,
            brand=brand,
            job_type='image',
            input_data=params,
            provider=params.get('provider', 'fal')
        )
        job = AIJobService.execute_job_sync(str(job.id))
        out = job.output_data
        
        media_item = Media.objects.create(
            user=user,
            workspace=workspace,
            brand=brand,
            file_name=out.get('file_name', 'ai_generated_image.png'),
            file_url=out.get('url', ''),
            file_size_bytes=1024 * 500,
            mime_type=out.get('mime_type', 'image/png'),
            tags=['AI Generated', params.get('aspect_ratio', '1:1'), params.get('style', 'default')]
        )
        return media_item


class AIVideoService:
    @staticmethod
    def generate_video(workspace, user, brand, params: Dict[str, Any]) -> Media:
        job = AIJobService.create_job(
            workspace=workspace,
            user=user,
            brand=brand,
            job_type='video',
            input_data=params,
            provider=params.get('provider', 'runway')
        )
        job = AIJobService.execute_job_sync(str(job.id))
        out = job.output_data

        media_item = Media.objects.create(
            user=user,
            workspace=workspace,
            brand=brand,
            file_name=out.get('file_name', 'ai_generated_video.mp4'),
            file_url=out.get('url', ''),
            file_size_bytes=1024 * 1024 * 5,
            mime_type='video/mp4',
            tags=['AI Video', params.get('aspect_ratio', '16:9')]
        )
        return media_item


class AIVoiceService:
    @staticmethod
    def generate_voiceover(workspace, user, brand, params: Dict[str, Any]) -> Dict[str, Any]:
        job = AIJobService.create_job(
            workspace=workspace,
            user=user,
            brand=brand,
            job_type='voiceover',
            input_data=params,
            provider=params.get('provider', 'murf')
        )
        job = AIJobService.execute_job_sync(str(job.id))
        out = job.output_data

        media_item = Media.objects.create(
            user=user,
            workspace=workspace,
            brand=brand,
            file_name=f"voiceover_{job.id}.mp3",
            file_url=out.get('audio_url', ''),
            mime_type='audio/mp3',
            tags=['AI Voiceover', params.get('voice_id', 'natalie')]
        )
        out['media_id'] = media_item.id
        return out
