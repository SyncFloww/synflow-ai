import os
import json
import time
from datetime import datetime
from django.db import models
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from google import genai
from google.genai import types

from content.models import Content, ContentVersion
from workspaces.models import Workspace, WorkspaceMember
from social.models import Brand, BrandVoice, BrandGuideline
from media.models import Media

from .models import (
    AIAgent, AgentTask, AIModel, PromptTemplate, GeneratedContent, ContentGeneration, GenerationHistory,
    AIJob, AIContentProject, AIScript, AIScriptVersion, AISocialContent,
    CustomVoiceProfile, VoiceConsent, AudioProject, AICaption, AIUsageRecord
)
from .serializers import (
    AIAgentSerializer, AgentTaskSerializer, AIModelSerializer, 
    PromptTemplateSerializer, GeneratedContentSerializer, 
    ContentGenerationSerializer, GenerationHistorySerializer,
    AIJobSerializer, AIContentProjectSerializer, AIScriptSerializer, AIScriptVersionSerializer,
    AISocialContentSerializer, CustomVoiceProfileSerializer, VoiceConsentSerializer,
    AudioProjectSerializer, AICaptionSerializer, AIUsageRecordSerializer
)
from .services.job_service import AIJobService
from .services.studio_services import (
    AIIdeaService, AIScriptService, AISocialContentService, AIImageService,
    AIVideoService, AIVoiceService
)
from .providers import VoiceProviderRegistry, LLMProviderRegistry

# Lazy-initialization helper for Gemini
def get_gemini_client():
    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_GENAI_API_KEY')
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception:
        return None

def get_user_workspace(request):
    ws_id = request.headers.get('X-Workspace-ID') or request.query_params.get('workspace') or request.data.get('workspace')
    if ws_id:
        try:
            return Workspace.objects.get(id=ws_id, members__user=request.user, members__status='ACTIVE')
        except Workspace.DoesNotExist:
            pass
    # Default to user's first owned or joined workspace
    member = WorkspaceMember.objects.filter(user=request.user, status='ACTIVE').first()
    if member:
        return member.workspace
    ws, _ = Workspace.objects.get_or_create(owner=request.user, defaults={'name': f"{request.user.username}'s Workspace"})
    WorkspaceMember.objects.get_or_create(workspace=ws, user=request.user, defaults={'role': 'OWNER', 'status': 'ACTIVE'})
    return ws


class AIAgentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AIAgent.objects.filter(is_active=True)
    serializer_class = AIAgentSerializer
    permission_classes = [permissions.IsAuthenticated]

class AgentTaskViewSet(viewsets.ModelViewSet):
    serializer_class = AgentTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AgentTask.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class AIModelViewSet(viewsets.ModelViewSet):
    serializer_class = AIModelSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = AIModel.objects.all()

class PromptTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = PromptTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PromptTemplate.objects.filter(
            models.Q(created_by=self.request.user) | models.Q(created_by__is_superuser=True)
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class GeneratedContentViewSet(viewsets.ModelViewSet):
    serializer_class = GeneratedContentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return GeneratedContent.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ContentGenerationViewSet(viewsets.ModelViewSet):
    serializer_class = ContentGenerationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ContentGeneration.objects.filter(user=self.request.user).order_by('-created_at')

class GenerationHistoryViewSet(viewsets.ModelViewSet):
    serializer_class = GenerationHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return GenerationHistory.objects.filter(user=self.request.user).order_by('-timestamp')

# --- AI MEDIA STUDIO EXTENDED VIEWS ---

class AIJobViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AIJobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        ws = get_user_workspace(self.request)
        return AIJob.objects.filter(workspace=ws).order_by('-created_at')

    @action(detail=True, methods=['post'], url_path='retry')
    def retry(self, request, pk=None):
        job = self.get_object()
        job.status = 'QUEUED'
        job.progress = 0
        job.error = ''
        job.retry_count += 1
        job.save()
        AIJobService.dispatch_job_async(str(job.id))
        return Response(AIJobSerializer(job).data)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        job = self.get_object()
        if job.status in ['QUEUED', 'PROCESSING']:
            job.status = 'CANCELLED'
            job.save()
        return Response(AIJobSerializer(job).data)


class AIContentProjectViewSet(viewsets.ModelViewSet):
    serializer_class = AIContentProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        ws = get_user_workspace(self.request)
        return AIContentProject.objects.filter(workspace=ws).order_by('-updated_at')

    def perform_create(self, serializer):
        ws = get_user_workspace(self.request)
        serializer.save(user=self.request.user, workspace=ws)


class AIScriptViewSet(viewsets.ModelViewSet):
    serializer_class = AIScriptSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        ws = get_user_workspace(self.request)
        return AIScript.objects.filter(workspace=ws).order_by('-updated_at')

    @action(detail=True, methods=['post'], url_path='version')
    def create_version(self, request, pk=None):
        script = self.get_object()
        change = request.data.get('change_summary', 'Version save')
        ver = AIScriptService.create_version(script, change)
        return Response(AIScriptVersionSerializer(ver).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='convert-social')
    def convert_to_social(self, request, pk=None):
        script = self.get_object()
        ws = script.workspace
        brand = script.brand
        social_items = AISocialContentService.convert_script_to_social(ws, request.user, brand, script)
        return Response(AISocialContentSerializer(social_items, many=True).data)


class AIIdeaGeneratorView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ws = get_user_workspace(request)
        brand_id = request.data.get('brand')
        brand = Brand.objects.filter(id=brand_id, workspace=ws).first() if brand_id else None
        
        job = AIIdeaService.generate_ideas(ws, request.user, brand, request.data)
        return Response(AIJobSerializer(job).data, status=status.HTTP_202_ACCEPTED)


class AIScriptGeneratorView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ws = get_user_workspace(request)
        brand_id = request.data.get('brand')
        brand = Brand.objects.filter(id=brand_id, workspace=ws).first() if brand_id else None
        
        script = AIScriptService.generate_script(ws, request.user, brand, request.data)
        return Response(AIScriptSerializer(script).data, status=status.HTTP_201_CREATED)


class AIImageGeneratorView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ws = get_user_workspace(request)
        brand_id = request.data.get('brand')
        brand = Brand.objects.filter(id=brand_id, workspace=ws).first() if brand_id else None
        
        media_item = AIImageService.generate_image(ws, request.user, brand, request.data)
        return Response({
            "id": media_item.id,
            "file_name": media_item.file_name,
            "file_url": media_item.file_url,
            "mime_type": media_item.mime_type,
            "workspace": media_item.workspace_id,
            "created_at": media_item.created_at
        }, status=status.HTTP_201_CREATED)


class AIVideoGeneratorView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ws = get_user_workspace(request)
        brand_id = request.data.get('brand')
        brand = Brand.objects.filter(id=brand_id, workspace=ws).first() if brand_id else None
        
        media_item = AIVideoService.generate_video(ws, request.user, brand, request.data)
        return Response({
            "id": media_item.id,
            "file_name": media_item.file_name,
            "file_url": media_item.file_url,
            "mime_type": media_item.mime_type,
            "workspace": media_item.workspace_id,
            "created_at": media_item.created_at
        }, status=status.HTTP_201_CREATED)


class AIVoiceStudioView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        prov = VoiceProviderRegistry.get('murf')
        voices = prov.list_voices()
        return Response({"voices": voices})

    def post(self, request):
        ws = get_user_workspace(request)
        brand_id = request.data.get('brand')
        brand = Brand.objects.filter(id=brand_id, workspace=ws).first() if brand_id else None
        
        result = AIVoiceService.generate_voiceover(ws, request.user, brand, request.data)
        return Response(result, status=status.HTTP_201_CREATED)


class CustomVoiceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        ws = get_user_workspace(request)
        profiles = CustomVoiceProfile.objects.filter(workspace=ws)
        return Response(CustomVoiceProfileSerializer(profiles, many=True).data)

    def post(self, request):
        ws = get_user_workspace(request)
        profile = CustomVoiceProfile.objects.create(
            workspace=ws,
            user=request.user,
            name=request.data.get('name', 'My Voice Profile'),
            description=request.data.get('description', ''),
            provider_voice_id=request.data.get('provider_voice_id', f"custom_{request.user.id}"),
            sample_url=request.data.get('sample_url', '')
        )
        return Response(CustomVoiceProfileSerializer(profile).data, status=status.HTTP_201_CREATED)


class VoiceConsentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ws = get_user_workspace(request)
        profile_id = request.data.get('voice_profile')
        profile = CustomVoiceProfile.objects.filter(id=profile_id, workspace=ws).first() if profile_id else None
        
        consent = VoiceConsent.objects.create(
            voice_profile=profile,
            user=request.user,
            workspace=ws,
            consent_statement=request.data.get('statement', 'I hereby grant explicit consent to train and use my voice profile for AI voice synthesis in Syncfloww.'),
            signature_name=request.data.get('signature_name', request.user.get_full_name() or request.user.username),
            ip_address=request.META.get('REMOTE_ADDR')
        )
        return Response(VoiceConsentSerializer(consent).data, status=status.HTTP_201_CREATED)


class AIAudioMixerView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ws = get_user_workspace(request)
        job = AIJobService.create_job(
            workspace=ws,
            user=request.user,
            job_type='audio_mix',
            input_data=request.data
        )
        job = AIJobService.execute_job_sync(str(job.id))
        return Response(AIJobSerializer(job).data)


class AICaptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ws = get_user_workspace(request)
        audio_url = request.data.get('audio_url', '')
        text = request.data.get('text', 'Syncfloww AI Media Studio creates viral social content.')
        
        words = text.split()
        timings = []
        t = 0.0
        for w in words:
            timings.append({"word": w, "start_time": round(t, 2), "end_time": round(t + 0.4, 2)})
            t += 0.4

        caption = AICaption.objects.create(
            workspace=ws,
            user=request.user,
            audio_url=audio_url,
            transcript=text,
            srt_content=f"1\n00:00:00,000 --> 00:00:05,000\n{text}",
            vtt_content=f"WEBVTT\n\n1\n00:00:00.000 --> 00:00:05.000\n{text}",
            word_timings=timings,
            style_config=request.data.get('style_config', {"font": "Inter", "color": "#FFFFFF", "position": "bottom"})
        )
        return Response(AICaptionSerializer(caption).data, status=status.HTTP_201_CREATED)


class AIMagicEditorView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        action_name = request.data.get('action', 'rewrite') # rewrite, expand, shorten, change_tone, viral_hook, make_professional
        text = request.data.get('text', '')
        tone = request.data.get('tone', 'engaging')
        
        llm = LLMProviderRegistry.get('gemini')
        prompt = f"Perform '{action_name}' action on the following text (desired tone: {tone}):\n\n'{text}'"
        res = llm.generate_text(prompt=prompt)
        
        return Response({
            "action": action_name,
            "original_text": text,
            "result_text": res.text,
            "estimated_cost": res.estimated_cost
        })


class AIUsageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        ws = get_user_workspace(request)
        records = AIUsageRecord.objects.filter(workspace=ws)
        total_cost = sum([r.estimated_cost for r in records])
        total_jobs = AIJob.objects.filter(workspace=ws).count()
        return Response({
            "total_estimated_cost": float(total_cost),
            "total_jobs_count": total_jobs,
            "usage_history": AIUsageRecordSerializer(records[:50], many=True).data
        })

# Legacy ExecuteAgent & GenerateContent backward compatibility
class ExecuteAgentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, agent_type):
        try:
            agent = AIAgent.objects.get(id=agent_type, is_active=True)
        except AIAgent.DoesNotExist:
            return Response({'error': f'Agent {agent_type} not found.'}, status=status.HTTP_404_NOT_FOUND)

        input_data = request.data.get('input_data', request.data)
        task = AgentTask.objects.create(
            user=request.user,
            agent=agent,
            agent_name=agent.name,
            input_data=input_data,
            status='processing'
        )

        llm = LLMProviderRegistry.get('gemini')
        prompt = f"Execute agent '{agent.name}' task for input: {json.dumps(input_data)}"
        res = llm.generate_text(prompt=prompt)
        
        task.status = 'completed'
        task.completed_at = datetime.now()
        task.output_data = res.structured_data if res.structured_data else {"result": res.text}
        task.save()
        return Response(AgentTaskSerializer(task).data)


class GenerateContentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        topic = request.data.get('topic', 'Content strategy')
        platform = request.data.get('platform', 'instagram')
        llm = LLMProviderRegistry.get('gemini')
        prompt = f"Create a viral {platform} post about {topic}"
        res = llm.generate_text(prompt=prompt)

        gen_content = GeneratedContent.objects.create(
            user=request.user,
            prompt_used=prompt,
            content_text=res.text,
            platform=platform
        )
        return Response(GeneratedContentSerializer(gen_content).data, status=status.HTTP_201_CREATED)
