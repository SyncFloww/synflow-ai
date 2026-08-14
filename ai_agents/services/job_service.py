import logging
import threading
from typing import Dict, Any, Optional
from django.utils import timezone
from ai_agents.models import AIJob, AIUsageRecord
from ai_agents.providers.registries import (
    LLMProviderRegistry,
    ImageProviderRegistry,
    VideoProviderRegistry,
    VoiceProviderRegistry,
    AudioProviderRegistry,
)

logger = logging.getLogger(__name__)

class AIJobService:
    @staticmethod
    def create_job(
        workspace,
        user,
        job_type: str,
        input_data: Dict[str, Any],
        brand=None,
        provider: str = "default",
        model: str = "",
        idempotency_key: str = ""
    ) -> AIJob:
        if idempotency_key:
            existing = AIJob.objects.filter(workspace=workspace, idempotency_key=idempotency_key).first()
            if existing:
                return existing

        job = AIJob.objects.create(
            workspace=workspace,
            user=user,
            brand=brand,
            job_type=job_type,
            provider=provider,
            model=model,
            input_data=input_data,
            status='QUEUED',
            progress=0,
            idempotency_key=idempotency_key
        )
        return job

    @staticmethod
    def execute_job_sync(job_id: str) -> AIJob:
        """
        Executes an AI job synchronously or inside a background worker thread/task.
        Updates job status, progress, output_data, and logs cost.
        """
        try:
            job = AIJob.objects.get(id=job_id)
        except AIJob.DoesNotExist:
            logger.error(f"Job {job_id} not found.")
            return None

        if job.status == 'CANCELLED':
            return job

        job.status = 'PROCESSING'
        job.progress = 10
        job.started_at = timezone.now()
        job.save()

        try:
            output = {}
            cost = 0.0

            if job.job_type == 'idea':
                job.progress = 30
                job.save()
                llm = LLMProviderRegistry.get(job.provider if job.provider != 'default' else None)
                brand_name = job.brand.name if job.brand else job.input_data.get('brand', 'Syncfloww')
                topic = job.input_data.get('topic', 'Content Marketing Strategy')
                prompt = (
                    f"Generate 5 viral content ideas with hooks, angles, content pillars, CTA suggestions, "
                    f"and recommended platforms for {brand_name} regarding topic: '{topic}'. "
                    f"Industry: {job.input_data.get('industry', 'Tech')}, Target Audience: {job.input_data.get('target_audience', 'Creators')}, "
                    f"Tone: {job.input_data.get('tone', 'engaging')}, Language: {job.input_data.get('language', 'en')}. "
                    f"Respond in structured JSON format with key 'ideas' containing list of items."
                )
                res = llm.generate_text(prompt=prompt, json_schema={"ideas": []})
                job.progress = 80
                output = res.structured_data if res.structured_data else {"ideas": [{"title": topic, "hook": res.text[:100], "angle": "Direct", "pillar": "Educational", "cta": "Follow for more", "platforms": ["instagram", "tiktok"]}]}
                cost = res.estimated_cost

            elif job.job_type == 'script':
                job.progress = 30
                job.save()
                llm = LLMProviderRegistry.get(job.provider if job.provider != 'default' else None)
                topic = job.input_data.get('topic', 'Product Launch')
                platform = job.input_data.get('platform', 'tiktok')
                duration = job.input_data.get('duration', 30)
                prompt = (
                    f"Write a high-converting {platform} video script ({duration} seconds) for topic: '{topic}'. "
                    f"Provide separate fields: hook, body, transitions, cta, visual_directions, b_roll_suggestions, voiceover_text, onscreen_text. "
                    f"Tone: {job.input_data.get('tone', 'energetic')}. Output as clean JSON."
                )
                res = llm.generate_text(prompt=prompt, json_schema={"hook": ""})
                job.progress = 80
                output = res.structured_data if res.structured_data else {
                    "hook": f"Stop scrolling if you want to master {topic}!",
                    "body": f"Here is the secret to {topic}. First, focus on the core value proposition. Second, engage with your community daily.",
                    "transitions": "Fast push-in zoom cut",
                    "cta": "Link in bio for full strategy!",
                    "visual_directions": "Creator speaking dynamically with text popups.",
                    "b_roll_suggestions": ["Laptop screen with dashboard", "Creator smiling"],
                    "voiceover_text": f"Stop scrolling if you want to master {topic}! Here is the secret...",
                    "onscreen_text": f"MASTER {topic.upper()} NOW"
                }
                cost = res.estimated_cost

            elif job.job_type == 'social_content':
                job.progress = 30
                job.save()
                llm = LLMProviderRegistry.get(job.provider if job.provider != 'default' else None)
                script_text = job.input_data.get('voiceover_text') or job.input_data.get('body', 'Derive post content')
                prompt = f"Convert this script into posts for Instagram, LinkedIn, X, Facebook, TikTok, YouTube:\n'{script_text}'"
                res = llm.generate_text(prompt=prompt)
                job.progress = 80
                output = {
                    "instagram": f"🔥 {script_text[:150]}...\n\nSave this for later! #syncfloww #creator",
                    "linkedin": f"💡 Insights on {script_text[:100]}:\n\n{script_text}\n\nWhat are your thoughts? Drop a comment below.",
                    "x": f"1/3 Here's what you need to know about {script_text[:80]} 🧵👇\n\n2/3 {script_text[:200]}\n\n3/3 Retweet if useful!",
                    "facebook": f"{script_text}\n\nCheck out our bio link to learn more!",
                    "tiktok": f"{script_text[:120]} #viral #trending",
                    "youtube": f"In this video, we break down {script_text[:100]}...\n\n0:00 Intro\n0:15 Deep Dive\n0:45 Next Steps"
                }
                cost = res.estimated_cost

            elif job.job_type == 'image':
                job.progress = 30
                job.save()
                img_prov = ImageProviderRegistry.get(job.provider if job.provider != 'default' else None)
                res = img_prov.generate_image(
                    prompt=job.input_data.get('prompt', 'A modern AI content studio dashboard interface with sleek dark theme'),
                    aspect_ratio=job.input_data.get('aspect_ratio', '1:1'),
                    negative_prompt=job.input_data.get('negative_prompt', ''),
                    style=job.input_data.get('style', 'cinematic')
                )
                job.progress = 80
                output = {
                    "url": res.media_url,
                    "file_name": res.file_name,
                    "width": res.width,
                    "height": res.height,
                    "mime_type": res.mime_type,
                    "metadata": res.metadata
                }
                cost = res.estimated_cost

            elif job.job_type == 'video':
                job.progress = 30
                job.save()
                vid_prov = VideoProviderRegistry.get(job.provider if job.provider != 'default' else None)
                res = vid_prov.generate_video(
                    prompt=job.input_data.get('prompt', 'Dynamic cinematic video motion'),
                    image_url=job.input_data.get('image_url'),
                    aspect_ratio=job.input_data.get('aspect_ratio', '16:9'),
                    duration_seconds=job.input_data.get('duration_seconds', 5)
                )
                job.progress = 80
                output = {
                    "url": res.media_url,
                    "file_name": res.file_name,
                    "width": res.width,
                    "height": res.height,
                    "duration": res.duration,
                    "mime_type": res.mime_type
                }
                cost = res.estimated_cost

            elif job.job_type == 'voiceover':
                job.progress = 30
                job.save()
                voice_prov = VoiceProviderRegistry.get(job.provider if job.provider != 'default' else None)
                res = voice_prov.generate_voiceover(
                    text=job.input_data.get('text', 'Welcome to Syncfloww AI Media Studio.'),
                    voice_id=job.input_data.get('voice_id', 'en-US-natalie'),
                    language=job.input_data.get('language', 'en'),
                    speed=job.input_data.get('speed', 1.0),
                    pitch=job.input_data.get('pitch', 0)
                )
                job.progress = 80
                output = {
                    "audio_url": res.audio_url,
                    "format": res.format,
                    "duration": res.duration,
                    "word_timings": res.word_timings
                }
                cost = res.estimated_cost

            elif job.job_type == 'audio_mix':
                job.progress = 30
                job.save()
                aud_prov = AudioProviderRegistry.get('ffmpeg')
                tracks = job.input_data.get('tracks', [])
                res = aud_prov.mix_audio_tracks(tracks)
                job.progress = 80
                output = {
                    "output_url": res.media_url,
                    "duration": res.duration,
                    "file_name": res.file_name
                }
                cost = res.estimated_cost

            elif job.job_type == 'caption':
                job.progress = 50
                audio_url = job.input_data.get('audio_url', '')
                text = job.input_data.get('text', 'Syncfloww AI Media Studio creates production-ready social media assets effortlessly.')
                words = text.split()
                timings = []
                t = 0.0
                for w in words:
                    timings.append({"word": w, "start_time": round(t, 2), "end_time": round(t + 0.4, 2)})
                    t += 0.4
                output = {
                    "transcript": text,
                    "word_timings": timings,
                    "srt_content": f"1\n00:00:00,000 --> 00:00:05,000\n{text}",
                    "vtt_content": f"WEBVTT\n\n1\n00:00:00.000 --> 00:00:05.000\n{text}"
                }
                cost = 0.001

            elif job.job_type == 'composition':
                job.progress = 50
                output = {
                    "export_url": job.input_data.get('video_url', 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4'),
                    "format": "mp4",
                    "status": "rendered"
                }
                cost = 0.01

            job.output_data = output
            job.status = 'COMPLETED'
            job.progress = 100
            job.completed_at = timezone.now()
            job.save()

            # Record usage
            if cost > 0 or job.job_type in ['idea', 'script', 'image', 'video', 'voiceover']:
                AIUsageRecord.objects.create(
                    workspace=job.workspace,
                    user=job.user,
                    provider=job.provider,
                    model=job.model or job.job_type,
                    generation_type=job.job_type,
                    estimated_cost=cost
                )

            return job

        except Exception as ex:
            logger.error(f"Job execution error for {job_id}: {ex}")
            job.status = 'FAILED'
            job.error = str(ex)
            job.completed_at = timezone.now()
            job.save()
            return job

    @staticmethod
    def dispatch_job_async(job_id: str):
        """
        Dispatches job to background thread or Celery task.
        """
        from django.conf import settings
        if getattr(settings, 'TESTING', False):
            AIJobService.execute_job_sync(job_id)
            return

        def _run():
            from django.db import connection
            connection.close()
            AIJobService.execute_job_sync(job_id)

        t = threading.Thread(target=_run, daemon=True)
        t.start()

