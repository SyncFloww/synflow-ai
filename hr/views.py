import os
import json
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from google import genai
from .models import Employee, LeaveRequest
from .serializers import EmployeeSerializer, LeaveRequestSerializer

def get_gemini_client():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

class EmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Employee.objects.filter(user=self.request.user).order_by('-performance_rating')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='recommend-hiring')
    def recommend_hiring(self, request):
        user = request.user
        employees = Employee.objects.filter(user=user)
        
        # Build prompt listing existing headcount to help the AI decide bottlenecks
        headcount = employees.count()
        depts = list(employees.values_list('department', flat=True).distinct())
        
        prompt = (
            f"As an AI HR Director, analyze the current team structure of our organization:\n"
            f"- Total Headcount: {headcount}\n"
            f"- Departments: {', '.join(depts) if depts else 'None defined yet (e.g. Sales, Marketing, Tech)'}\n"
            f"Predict the next critical hiring roles we need to support 3x business scaling.\n"
            f"Provide role names, department recommendation, estimated salary budget, and reasoning.\n"
            f"Format strictly as a JSON object with keys: "
            f"'suggested_hires' (list of objects with keys: 'role', 'department', 'estimated_salary', 'reason')."
        )

        client = get_gemini_client()
        result = {
            "suggested_hires": [
                {
                    "role": "Lead Backend Engineer (Django/SaaS specialist)",
                    "department": "Engineering / Platform OS",
                    "estimated_salary": 120000,
                    "reason": "Needed to develop high-performance database microservices and modular monolith integrations as the customer base scales."
                },
                {
                    "role": "Customer Success Manager",
                    "department": "Customer Operations",
                    "estimated_salary": 70000,
                    "reason": "To proactively support high-value enterprise accounts, manage renewal schedules, and keep risk status at a minimum."
                }
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
                print(f"Failed to generate HR suggestions: {e}")

        return Response(result, status=status.HTTP_200_OK)

class LeaveRequestViewSet(viewsets.ModelViewSet):
    serializer_class = LeaveRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return LeaveRequest.objects.filter(user=self.request.user).order_by('-start_date')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
