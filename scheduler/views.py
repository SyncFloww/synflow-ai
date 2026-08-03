from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import CalendarEvent, Schedule
from .serializers import CalendarEventSerializer, ScheduleSerializer

class CalendarEventViewSet(viewsets.ModelViewSet):
    serializer_class = CalendarEventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CalendarEvent.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = ScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Schedule.objects.filter(user=self.request.user).order_by('scheduled_time')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        schedule = self.get_object()
        if schedule.status != 'pending':
            return Response({'error': 'Only pending schedules can be cancelled.'}, status=status.HTTP_400_BAD_REQUEST)
        schedule.delete()
        return Response({'status': 'schedule cancelled and removed'}, status=status.HTTP_200_OK)
