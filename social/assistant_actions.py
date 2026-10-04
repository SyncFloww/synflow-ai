from django.db import transaction
from django.utils import timezone
from rest_framework import status, serializers
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from workspaces.permissions import get_user_workspace_role
from ai_agents.services.job_service import AIJobService
from .models import BrandMessage, BrandKnowledge, Brand, BrandLead
from .assistant import AssistantInput, respond, extract_document

class BrandAssistantActions:
    def require_brand_manager(self, brand):
        if get_user_workspace_role(self.request.user, brand.workspace) not in ('OWNER', 'ADMIN', 'MANAGER'):
            raise PermissionDenied('Only brand managers can make this change.')

    @action(detail=True, methods=['get', 'post', 'delete'], url_path='assistant')
    def assistant(self, request, pk=None):
        brand = self.get_object()
        if request.method == 'GET':
            recent = list(brand.messages.order_by('-created_at', '-id')[:100])
            return Response([{'id': m.id, 'role': m.role, 'content': m.content, 'created_at': m.created_at} for m in reversed(recent)])
        self.require_brand_manager(brand)
        if request.method == 'DELETE':
            brand.messages.all().delete()
            return Response(status=204)
        serializer = AssistantInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        job = AIJobService.create_job(brand.workspace, request.user, 'brand_assistant', {'mode': payload['mode']}, brand=brand)
        history = list(brand.messages.order_by('-created_at', '-id').values('role', 'content')[:12])
        try:
            answer = respond(brand, payload, list(reversed(history)))
            with transaction.atomic():
                BrandMessage.objects.create(brand=brand, user=request.user, role='user', content=payload['message'])
                message = BrandMessage.objects.create(brand=brand, user=request.user, role='assistant', content=answer['reply'])
                job.status = 'COMPLETED'
                job.progress = 100
                job.completed_at = timezone.now()
                job.save(update_fields=['status', 'progress', 'completed_at'])
            return Response({**answer, 'id': message.id}, status=201)
        except Exception:
            job.status = 'FAILED'
            job.error = 'Assistant request failed.'
            job.completed_at = timezone.now()
            job.save(update_fields=['status', 'error', 'completed_at'])
            raise

    @action(detail=True, methods=['post'], url_path='documents', parser_classes=[MultiPartParser, FormParser])
    def documents(self, request, pk=None):
        brand = self.get_object()
        self.require_brand_manager(brand)
        upload = request.FILES.get('file')
        if not upload:
            raise ValidationError({'file': 'Choose a document.'})
        if request.data.get('consent') != 'true':
            raise ValidationError({'consent': 'Confirm that this document may be used as brand context.'})
        text = extract_document(upload)
        with transaction.atomic():
            Brand.objects.select_for_update().get(pk=brand.pk)
            if brand.knowledge_items.filter(is_active=True).count() >= 20:
                raise ValidationError('This brand has reached the 20-reference limit. Delete an unused reference first.')
            item = BrandKnowledge.objects.create(brand=brand, title=upload.name[:255], content=text, knowledge_type='OTHER')
        return Response({'id': item.id, 'title': item.title, 'content': item.content, 'created_at': item.created_at}, status=201)

    @action(detail=True, methods=['delete'], url_path=r'documents/(?P<document_id>\d+)')
    def delete_document(self, request, pk=None, document_id=None):
        brand = self.get_object()
        self.require_brand_manager(brand)
        from django.shortcuts import get_object_or_404
        item = get_object_or_404(BrandKnowledge, pk=document_id, brand=brand)
        item.delete()
        return Response(status=204)

    @action(detail=True, methods=['get', 'post'], url_path='leads')
    def leads(self, request, pk=None):
        brand = self.get_object()
        self.require_brand_manager(brand)
        if request.method == 'GET':
            return Response(list(brand.leads.values('id', 'name', 'email', 'source', 'note', 'consent_at', 'created_at')[:500]))
        class LeadInput(serializers.Serializer):
            name = serializers.CharField(max_length=255)
            email = serializers.EmailField()
            source = serializers.CharField(max_length=255)
            note = serializers.CharField(max_length=2000, allow_blank=True, default='')
            consent = serializers.BooleanField()
        data = LeadInput(data=request.data)
        data.is_valid(raise_exception=True)
        values = data.validated_data
        if values.pop('consent') is not True:
            raise ValidationError({'consent': 'Record a contact only after they agree to follow-up.'})
        lead = BrandLead.objects.create(brand=brand, created_by=request.user, consent_at=timezone.now(), **values)
        return Response({'id': lead.id}, status=201)

    @action(detail=True, methods=['delete'], url_path=r'leads/(?P<lead_id>\d+)')
    def delete_lead(self, request, pk=None, lead_id=None):
        brand = self.get_object()
        self.require_brand_manager(brand)
        from django.shortcuts import get_object_or_404
        get_object_or_404(BrandLead, brand=brand, pk=lead_id).delete()
        return Response(status=204)
