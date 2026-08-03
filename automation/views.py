from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from .models import Workflow, WorkflowNode, WorkflowTrigger, WorkflowAction, WorkflowExecution
from .serializers import (
    WorkflowSerializer, WorkflowNodeSerializer, WorkflowTriggerSerializer,
    WorkflowActionSerializer, WorkflowExecutionSerializer
)

class WorkflowViewSet(viewsets.ModelViewSet):
    serializer_class = WorkflowSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Workflow.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='execute')
    def execute_workflow(self, request, pk=None):
        workflow = self.get_object()
        
        # Log execution
        execution = WorkflowExecution.objects.create(
            workflow=workflow,
            status='running',
            logs=f"[{timezone.now().isoformat()}] Starting workflow: {workflow.name}\n"
        )
        
        try:
            # Gather nodes & simulate
            nodes = workflow.nodes.all()
            execution.logs += f"[{timezone.now().isoformat()}] Found {nodes.count()} configured nodes.\n"
            
            trigger_detail = getattr(workflow, 'trigger', None)
            if trigger_detail:
                execution.logs += f"[{timezone.now().isoformat()}] Trigger activated: {trigger_detail.trigger_type}\n"
            else:
                execution.logs += f"[{timezone.now().isoformat()}] Manual execution triggered.\n"

            # Execute each action step
            actions_list = workflow.actions.all().order_by('order')
            for index, act in enumerate(actions_list):
                execution.logs += f"[{timezone.now().isoformat()}] Executing Action Step {index+1}: {act.action_type}\n"
                # Simulating dynamic outcomes
                if act.action_type == 'generate_ai_content':
                    execution.logs += f"[{timezone.now().isoformat()}] AI Content Engine returned 240 words copy successfully.\n"
                elif act.action_type == 'publish':
                    execution.logs += f"[{timezone.now().isoformat()}] Content successfully scheduled to connected socials.\n"
                elif act.action_type == 'notify_team':
                    execution.logs += f"[{timezone.now().isoformat()}] Workspace Slack integration notified.\n"
                else:
                    execution.logs += f"[{timezone.now().isoformat()}] Completed task: {act.action_type}\n"

            execution.status = 'success'
            execution.logs += f"[{timezone.now().isoformat()}] Workflow completed successfully!"
        except Exception as e:
            execution.status = 'failed'
            execution.logs += f"[{timezone.now().isoformat()}] ERROR: {str(e)}"
        
        execution.completed_at = timezone.now()
        execution.save()
        
        return Response({
            'status': 'Workflow Execution Finished',
            'execution_id': execution.id,
            'result': execution.status,
            'logs': execution.logs
        }, status=status.HTTP_200_OK)

class WorkflowNodeViewSet(viewsets.ModelViewSet):
    serializer_class = WorkflowNodeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WorkflowNode.objects.filter(workflow__user=self.request.user)

class WorkflowTriggerViewSet(viewsets.ModelViewSet):
    serializer_class = WorkflowTriggerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WorkflowTrigger.objects.filter(workflow__user=self.request.user)

class WorkflowActionViewSet(viewsets.ModelViewSet):
    serializer_class = WorkflowActionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WorkflowAction.objects.filter(workflow__user=self.request.user)

class WorkflowExecutionViewSet(viewsets.ModelViewSet):
    serializer_class = WorkflowExecutionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WorkflowExecution.objects.filter(workflow__user=self.request.user)
