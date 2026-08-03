from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.test import APITestCase

from workspaces.models import Workspace, WorkspaceMember
from social.models import Brand
from campaigns.models import (
    Campaign, CampaignStep, CampaignExecution, CampaignTemplate,
    CampaignGoal, CampaignBudget, CampaignAnalytics
)
from campaigns.services import CampaignWorkflowService

class CampaignWorkflowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='campuser', email='camp@example.com', password='Password123!')
        self.client.force_authenticate(user=self.user)
        self.workspace = Workspace.objects.create(name='Campaign WS', owner=self.user)
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.user, role='OWNER', status='ACTIVE')
        self.brand = Brand.objects.create(name='Campaign Brand', workspace=self.workspace, created_by=self.user)

    def test_campaign_template_instantiation_and_execution(self):
        template = CampaignTemplate.objects.create(
            user=self.user,
            name='Product Launch Template',
            description='Template for launching new features',
            structure={
                'steps': [
                    {
                        'name': 'Generate Launch Teaser',
                        'step_type': 'content_generation',
                        'config': {'prompt': 'Announce our new product feature', 'platform': 'instagram'}
                    },
                    {
                        'name': 'Publish Launch Post',
                        'step_type': 'publish_now',
                        'config': {'caption': 'We are live with product feature!', 'platforms': ['instagram']}
                    },
                    {
                        'name': 'Sync Launch Analytics',
                        'step_type': 'analytics_sync',
                        'config': {}
                    }
                ]
            }
        )

        campaign = CampaignWorkflowService.create_campaign_from_template(
            template=template,
            user=self.user,
            name='Feature Launch 2026',
            workspace=self.workspace,
            brand=self.brand
        )

        self.assertEqual(campaign.name, 'Feature Launch 2026')
        self.assertEqual(campaign.steps.count(), 3)

        execution = CampaignWorkflowService.execute_campaign(campaign)
        self.assertEqual(execution.status, 'completed')
        self.assertEqual(execution.runs.count(), 3)
        self.assertTrue(execution.logs.filter(level='info').exists())

    def test_campaign_api_endpoints(self):
        # Create Campaign via API
        url = '/api/campaigns/campaigns/'
        response = self.client.post(url, {
            'name': 'API Campaign',
            'description': 'Test campaign description',
            'brand': self.brand.id,
            'workspace': self.workspace.id,
            'budget': 5000.00
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        campaign_id = response.data['id']

        # Add Step
        step_url = '/api/campaigns/steps/'
        step_res = self.client.post(step_url, {
            'campaign': campaign_id,
            'step_number': 1,
            'name': 'Step 1 Content',
            'step_type': 'content_generation',
            'config': {'prompt': 'Sample prompt'}
        }, format='json')
        self.assertEqual(step_res.status_code, status.HTTP_201_CREATED)

        # Execute Campaign
        exec_url = f'/api/campaigns/campaigns/{campaign_id}/execute/'
        exec_res = self.client.post(exec_url)
        self.assertEqual(exec_res.status_code, status.HTTP_200_OK)
        self.assertEqual(exec_res.data['status'], 'completed')
