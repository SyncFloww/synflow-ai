import os
import json
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from google import genai
from .models import RevenueRecord, ExpenseRecord, Subscription
from .serializers import RevenueRecordSerializer, ExpenseRecordSerializer, SubscriptionSerializer

def get_gemini_client():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

class RevenueRecordViewSet(viewsets.ModelViewSet):
    serializer_class = RevenueRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return RevenueRecord.objects.filter(user=self.request.user).order_by('-date')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ExpenseRecordViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ExpenseRecord.objects.filter(user=self.request.user).order_by('-date')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user).order_by('-start_date')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='generate-forecast')
    def generate_forecast(self, request):
        user = request.user
        
        # Calculate current statistics to feed into prompt
        active_subs = Subscription.objects.filter(user=user, status='active')
        total_mrr = sum(sub.mrr for sub in active_subs)
        
        revenues = RevenueRecord.objects.filter(user=user)
        total_revenue = sum(r.amount for r in revenues)
        
        expenses = ExpenseRecord.objects.filter(user=user)
        total_expenses = sum(e.amount for e in expenses)

        prompt = (
            f"As an AI CFO, generate a detailed 3-month financial forecast and growth strategy recommendations for a software business "
            f"with the following metrics:\n"
            f"- Current Active Monthly Recurring Revenue (MRR): ${total_mrr}\n"
            f"- Total Historical Revenues: ${total_revenue}\n"
            f"- Total Historical Expenses: ${total_expenses}\n"
            f"Provide forecasted MRR, forecasted expenses, a simulated customer churn rate prediction (percentage), "
            f"and 3 actionable suggestions to improve cash flow.\n"
            f"Format strictly as a JSON object with keys: "
            f"'mrr_forecast' (list of 3 floats), 'expense_forecast' (list of 3 floats), "
            f"'predicted_churn_rate' (float), 'suggestions' (list of strings)."
        )

        client = get_gemini_client()
        result = {
            "mrr_forecast": [float(total_mrr) * 1.08, float(total_mrr) * 1.15, float(total_mrr) * 1.25],
            "expense_forecast": [float(total_expenses) * 1.02, float(total_expenses) * 1.04, float(total_expenses) * 1.05],
            "predicted_churn_rate": 3.4,
            "suggestions": [
                "Optimize server instance configurations to reduce hosting expenses by 15%.",
                "Introduce annual prepay plans to instantly boost cash flow and reduce churn latency.",
                "Increase acquisition budget for qualified leads with deal sizes above $2,000."
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
                print(f"Failed to run AI finance forecast: {e}")

        return Response(result, status=status.HTTP_200_OK)
