from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WorkflowViewSet, WorkflowNodeViewSet, WorkflowTriggerViewSet,
    WorkflowActionViewSet, WorkflowExecutionViewSet
)

router = DefaultRouter()
router.register(r'workflows', WorkflowViewSet, basename='workflow')
router.register(r'nodes', WorkflowNodeViewSet, basename='workflownode')
router.register(r'triggers', WorkflowTriggerViewSet, basename='workflowtrigger')
router.register(r'actions', WorkflowActionViewSet, basename='workflowaction')
router.register(r'executions', WorkflowExecutionViewSet, basename='workflowexecution')

urlpatterns = [
    path('', include(router.urls)),
]
