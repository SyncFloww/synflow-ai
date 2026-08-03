import os
import json
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from google import genai
from .models import SupportTicket, CustomerHealth
from .serializers import SupportTicketSerializer, CustomerHealthSerializer

def get_gemini_client():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

class SupportTicketViewSet(viewsets.ModelViewSet):
    serializer_class = SupportTicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SupportTicket.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='suggest-reply')
    def suggest_reply(self, request, pk=None):
        ticket = self.get_object()
        
        prompt = (
            f"As an automated customer support agent, generate a polite, highly empathetic, and professional draft response to solve this customer ticket:\n"
            f"Customer: {ticket.customer_name}\n"
            f"Ticket: {ticket.title}\n"
            f"Description: {ticket.description}\n"
            f"Generate a customized reply draft (string) and 3 potential quick actions to take.\n"
            f"Format strictly as a JSON object with keys: 'reply_draft' (string), 'quick_actions' (list of strings)."
        )

        client = get_gemini_client()
        result = {
            "reply_draft": f"Hi {ticket.customer_name},\n\nThank you for reaching out, and I am sincerely sorry to hear you're experiencing issues with {ticket.title}. Our team is looking into this immediately, and we'll resolve this for you shortly.",
            "quick_actions": [
                "Assign ticket to Senior Support Engineer.",
                "Verify customer environment logs.",
                "Send standard 24-hour SLA confirmation."
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
                print(f"Failed to generate ticket suggestion: {e}")

        return Response(result, status=status.HTTP_200_OK)

class CustomerHealthViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerHealthSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CustomerHealth.objects.filter(user=self.request.user).order_by('-health_score')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
