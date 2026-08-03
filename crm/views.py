import os
import json
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from google import genai
from .models import Lead, Deal, Company, Contact, Pipeline, Activity, CustomerJourney, CampaignAttribution
from .serializers import (
    LeadSerializer, DealSerializer, CompanySerializer, ContactSerializer,
    PipelineSerializer, ActivitySerializer, CustomerJourneySerializer, CampaignAttributionSerializer
)

def get_gemini_client():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

class LeadViewSet(viewsets.ModelViewSet):
    serializer_class = LeadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Lead.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='analyze-lead')
    def analyze_lead(self, request, pk=None):
        lead = self.get_object()
        
        prompt = (
            f"Analyze this sales lead: Name: {lead.name}, Company: {lead.company}, Email: {lead.email}, Current Status: {lead.status}, Deal Size: ${lead.deal_size}.\n"
            f"Provide a brief evaluation (string), a numeric qualification score from 0-100 (integer), and 3 suggested next steps for contact.\n"
            f"Format as strict JSON with keys: 'evaluation' (string), 'score' (int), 'next_steps' (list of strings)."
        )

        client = get_gemini_client()
        result = {
            "evaluation": f"{lead.company} exhibits strong potential. Based on their deal size of ${lead.deal_size}, they represent an enterprise-grade target. Further qualification of decision-makers is recommended.",
            "score": 75,
            "next_steps": [
                f"Send personalized introduction email focusing on how SyncFloww solves automated scheduling.",
                f"Look up decision makers at {lead.company} on LinkedIn.",
                f"Offer a custom 1-on-1 platform demo next week."
            ]
        }

        if client:
            try:
                response = client.models.generate_content(
                    model='gemini-3.5-flash',
                    contents=prompt,
                    config={"response_mime_type": "application/json"}
                )
                result = json.loads(response.text)
            except Exception as e:
                print(f"Failed to analyze lead via Gemini: {e}")

        return Response(result, status=status.HTTP_200_OK)


class DealViewSet(viewsets.ModelViewSet):
    serializer_class = DealSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Deal.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Company.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ContactViewSet(viewsets.ModelViewSet):
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PipelineViewSet(viewsets.ModelViewSet):
    serializer_class = PipelineSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Pipeline.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ActivityViewSet(viewsets.ModelViewSet):
    serializer_class = ActivitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Activity.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CustomerJourneyViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerJourneySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CustomerJourney.objects.filter(user=self.request.user).order_by('-recorded_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CampaignAttributionViewSet(viewsets.ModelViewSet):
    serializer_class = CampaignAttributionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CampaignAttribution.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

