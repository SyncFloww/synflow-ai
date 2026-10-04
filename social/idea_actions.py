from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from ai_agents.services.configured_llm import generate_text, AIUnavailable
from ai_agents.services.job_service import AIJobService
from ai_agents.services.prompt_manager import PromptManager
from .models import BrandIdea

class IdeaSerializer(serializers.ModelSerializer):
    hook = serializers.CharField(max_length=2000)
    angle = serializers.CharField(max_length=2000)
    cta = serializers.CharField(max_length=1000)
    platform = serializers.ChoiceField(choices=['instagram', 'tiktok', 'youtube', 'linkedin', 'facebook', 'x'])
    class Meta:
        model = BrandIdea
        fields = ['id', 'title', 'hook', 'angle', 'cta', 'platform', 'approved_at', 'created_at', 'updated_at']
        read_only_fields = ['id', 'approved_at', 'created_at', 'updated_at']

class IdeaRequest(serializers.Serializer):
    topic = serializers.CharField(max_length=255)
    platform = serializers.ChoiceField(choices=['instagram', 'tiktok', 'youtube', 'linkedin', 'facebook', 'x'], default='instagram')

class BrandIdeaActions:
    @action(detail=True, methods=['get', 'post'], url_path='ideas')
    def ideas(self, request, pk=None):
        brand = self.get_object()
        if request.method == 'GET':
            return Response(IdeaSerializer(brand.ideas.all()[:200], many=True).data)
        self.require_brand_manager(brand)
        data = IdeaSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        data.save(brand=brand)
        return Response(data.data, status=201)

    @action(detail=True, methods=['post'], url_path='ideas/generate')
    def generate_ideas(self, request, pk=None):
        brand = self.get_object()
        self.require_brand_manager(brand)
        data = IdeaRequest(data=request.data)
        data.is_valid(raise_exception=True)
        job = AIJobService.create_job(brand.workspace, request.user, 'idea', data.validated_data, brand=brand)
        try:
            values = data.validated_data
            result = generate_text(
                f"Propose exactly 5 distinct content ideas about {values['topic']} for {values['platform']}. "
                'Return JSON with ideas array. Each item has title, hook, angle, cta (strings). '
                'Ideas must fit the brand goal and use supported facts. Do not promise virality.',
                PromptManager().build_system_prompt(brand=brand, platform=values['platform']), json_output=True,
            ).structured_data
            items = result.get('ideas')
            if not isinstance(items, list) or len(items) != 5:
                raise AIUnavailable('The AI returned incomplete ideas. Try again.')
            validated = []
            for item in items:
                if not isinstance(item, dict):
                    raise AIUnavailable('The AI returned incomplete ideas. Try again.')
                # Model output must never be coerced into arbitrary text values.
                if any(not isinstance(item.get(k), str) for k in ('title', 'hook', 'angle', 'cta')):
                    raise AIUnavailable('The AI returned incomplete ideas. Try again.')
                serializer = IdeaSerializer(data={**item, 'platform': values['platform']})
                if not serializer.is_valid():
                    raise AIUnavailable('The AI returned incomplete ideas. Try again.')
                validated.append(serializer)
            with transaction.atomic():
                saved = [item.save(brand=brand) for item in validated]
                job.status = 'COMPLETED'
                job.progress = 100
                job.completed_at = timezone.now()
                job.save(update_fields=['status', 'progress', 'completed_at'])
            return Response(IdeaSerializer(saved, many=True).data, status=201)
        except Exception:
            job.status = 'FAILED'
            job.error = 'Idea generation failed.'
            job.completed_at = timezone.now()
            job.save(update_fields=['status', 'error', 'completed_at'])
            raise

    @action(detail=True, methods=['patch', 'delete'], url_path=r'ideas/(?P<idea_id>\d+)')
    def edit_idea(self, request, pk=None, idea_id=None):
        brand = self.get_object()
        self.require_brand_manager(brand)
        with transaction.atomic():
            idea = get_object_or_404(BrandIdea.objects.select_for_update(), pk=idea_id, brand=brand)
            if request.method == 'DELETE':
                idea.delete()
                return Response(status=204)
            data = IdeaSerializer(idea, data=request.data, partial=True)
            data.is_valid(raise_exception=True)
            data.save(approved_at=None, approved_by=None)
            return Response(data.data)

    @action(detail=True, methods=['post'], url_path=r'ideas/(?P<idea_id>\d+)/approve')
    def approve_idea(self, request, pk=None, idea_id=None):
        brand = self.get_object()
        self.require_brand_manager(brand)
        with transaction.atomic():
            idea = get_object_or_404(BrandIdea.objects.select_for_update(), pk=idea_id, brand=brand)
            if not all(getattr(idea, k).strip() for k in ('title', 'hook', 'angle', 'cta')):
                raise ValidationError('Complete the idea before approving it.')
            idea.approved_at = timezone.now()
            idea.approved_by = request.user
            idea.save(update_fields=['approved_at', 'approved_by', 'updated_at'])
            return Response(IdeaSerializer(idea).data)
