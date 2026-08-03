from rest_framework import serializers
from .models import Workflow, WorkflowNode, WorkflowTrigger, WorkflowAction, WorkflowExecution

class WorkflowNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowNode
        fields = '__all__'

class WorkflowTriggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowTrigger
        fields = '__all__'

class WorkflowActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowAction
        fields = '__all__'

class WorkflowExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowExecution
        fields = '__all__'

class WorkflowSerializer(serializers.ModelSerializer):
    nodes = WorkflowNodeSerializer(many=True, read_only=True)
    trigger = WorkflowTriggerSerializer(read_only=True)
    actions = WorkflowActionSerializer(many=True, read_only=True)
    executions = WorkflowExecutionSerializer(many=True, read_only=True)

    class Meta:
        model = Workflow
        fields = ['id', 'user', 'name', 'description', 'is_active', 'nodes', 'trigger', 'actions', 'executions', 'created_at', 'updated_at']
        read_only_fields = ['user']
