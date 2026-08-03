import os
import json
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from google import genai
from .models import ExecutiveMeeting
from .serializers import ExecutiveMeetingSerializer

# Import other apps' models if they exist to compile metrics
from crm.models import Lead, Deal
from finance.models import Subscription, RevenueRecord, ExpenseRecord
from hr.models import Employee

def get_gemini_client():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

class ExecutiveMeetingViewSet(viewsets.ModelViewSet):
    serializer_class = ExecutiveMeetingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ExecutiveMeeting.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='hold-meeting')
    def hold_meeting(self, request):
        user = request.user
        meeting_type = request.data.get('meeting_type', 'weekly')
        
        # Gather metrics across the Business OS Monolith
        leads_count = Lead.objects.filter(user=user).count()
        deals_count = Deal.objects.filter(user=user).count()
        total_mrr = sum(sub.mrr for sub in Subscription.objects.filter(user=user, status='active'))
        total_headcount = Employee.objects.filter(user=user).count()

        title = f"AI Board Room: {meeting_type.capitalize()} Strategic Review"

        prompt = (
            f"Hold a virtual AI Board of Directors Meeting for a scaling enterprise software company with these metrics:\n"
            f"- Active Monthly Recurring Revenue (MRR): ${total_mrr}\n"
            f"- Headcount: {total_headcount} employees\n"
            f"- Sales Pipeline: {leads_count} Leads, {deals_count} Active Deals\n"
            f"\n"
            f"Generate a creative conversational transcript between the following participants:\n"
            f"1. Eleanor Vance (AI CEO) - Moderator\n"
            f"2. Marcus Sterling (AI CFO) - Focused on ARR/MRR and burn rate\n"
            f"3. Sarah Jenkins (AI CMO) - Focused on campaigns and sales conversions\n"
            f"4. Dr. Aris Thorne (AI CTO) - Focused on developer platform and APIs\n"
            f"5. Clara Moss (AI HR Manager) - Focused on talent growth\n"
            f"\n"
            f"Format the output strictly as a JSON object with keys:\n"
            f"'transcript' (string with dialogues in markdown format, e.g. '**Eleanor (CEO):** Welcome everyone...'), "
            f"'summary' (string summarizing the conclusions), "
            f"'recommendations' (list of strings with concrete strategic priorities)."
        )

        client = get_gemini_client()
        result = {
            "transcript": (
                "**Eleanor (CEO):** Welcome, team, to our weekly executive alignment session. Today, we review our key metrics. Marcus, what's our financial standing?\n\n"
                f"**Marcus (CFO):** Thank you, Eleanor. We are currently sitting at **${total_mrr}/mo** in active MRR. Expenses are stable, but we should focus on converting our larger pipeline deals to ensure cash flow velocity remains high.\n\n"
                f"**Sarah (CMO):** On the customer acquisition side, we've logged **{leads_count} new leads** and **{deals_count} active deals** in the CRM. The marketing campaigns are driving traffic, but we'll benefit from Aris's new API tools to capture developer integrations.\n\n"
                "**Aris (CTO):** Agreed, Sarah. The developer dashboard and webhook integrations are built. Adding SDK configurations will allow external SaaS providers to plug in, increasing subscription retention.\n\n"
                f"**Clara (HR):** Headcount is currently at **{total_headcount}**. We should target hiring a customer success manager to assist Sarah with enterprise clients."
            ),
            "summary": f"The executive board reviewed the business performance. MRR stands at ${total_mrr} with a strong sales pipeline of {leads_count} leads. Focus is shifted toward closing deals and expanding developer API features.",
            "recommendations": [
                "Deploy the Developer Platform endpoints to start accepting external developer webhooks.",
                "Target the top 3 deals in the CRM pipeline for closing by offering premium custom onboarding.",
                "Review employee leave balances to prevent development velocity bottlenecks."
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
                print(f"Failed to hold board meeting: {e}")

        meeting = ExecutiveMeeting.objects.create(
            user=user,
            title=title,
            meeting_type=meeting_type,
            transcript=result["transcript"],
            summary=result["summary"],
            recommendations=result["recommendations"]
        )

        return Response(ExecutiveMeetingSerializer(meeting).data, status=status.HTTP_201_CREATED)
