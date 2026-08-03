from typing import Dict, Any, List, Optional
from django.utils import timezone
from django.db import transaction

from .models import (
    Campaign, CampaignStep, CampaignExecution,
    CampaignRun, CampaignLog, CampaignTemplate, CampaignGoal, CampaignBudget, CampaignAnalytics
)
from ai_agents.services import ContentGeneratorService
from publishing.services import PublishingService
from analytics.services import MetricsCollector
from social.models import SocialAccount

class CampaignWorkflowService:
    """
    Executes campaigns & step-by-step workflow automation pipelines.
    Supports:
    Campaign -> Multiple Content Items -> Scheduling -> Publishing -> Analytics Collection -> Execution History
    """

    @staticmethod
    def create_campaign_from_template(template: CampaignTemplate, user, name: str, workspace=None, brand=None) -> Campaign:
        with transaction.atomic():
            campaign = Campaign.objects.create(
                user=user,
                workspace=workspace or (brand.workspace if brand else None),
                brand=brand,
                name=name,
                description=template.description,
                status='draft'
            )
            CampaignBudget.objects.get_or_create(campaign=campaign)
            CampaignAnalytics.objects.get_or_create(campaign=campaign)

            steps_data = template.structure.get('steps', [])
            for idx, s in enumerate(steps_data, start=1):
                CampaignStep.objects.create(
                    campaign=campaign,
                    step_number=idx,
                    name=s.get('name', f'Step {idx}'),
                    step_type=s.get('step_type', 'content_generation'),
                    config=s.get('config', {})
                )

        return campaign

    @staticmethod
    def execute_campaign(campaign: Campaign) -> CampaignExecution:
        with transaction.atomic():
            execution = CampaignExecution.objects.create(
                campaign=campaign,
                status='running',
                started_at=timezone.now()
            )
            campaign.status = 'active'
            campaign.save()

            CampaignLog.objects.create(
                execution=execution,
                level='info',
                message=f"Started execution of campaign: {campaign.name}"
            )

        steps = campaign.steps.all()
        execution_failed = False

        for step in steps:
            run = CampaignRun.objects.create(
                execution=execution,
                step=step,
                status='running',
                started_at=timezone.now()
            )

            try:
                out = CampaignWorkflowService._run_step(campaign, step, execution)
                run.status = 'completed'
                run.output = out
                run.completed_at = timezone.now()
                run.save()

                CampaignLog.objects.create(
                    execution=execution,
                    level='info',
                    message=f"Step {step.step_number} ({step.name}) completed successfully."
                )
            except Exception as e:
                execution_failed = True
                run.status = 'failed'
                run.error_message = str(e)
                run.completed_at = timezone.now()
                run.save()

                CampaignLog.objects.create(
                    execution=execution,
                    level='error',
                    message=f"Step {step.step_number} ({step.name}) failed: {str(e)}"
                )
                break

        if execution_failed:
            execution.status = 'failed'
            campaign.status = 'paused'
        else:
            execution.status = 'completed'
            campaign.status = 'completed'

        execution.completed_at = timezone.now()
        execution.save()
        campaign.save()

        return execution

    @staticmethod
    def _run_step(campaign: Campaign, step: CampaignStep, execution: CampaignExecution) -> Dict[str, Any]:
        config = step.config or {}

        if step.step_type == 'content_generation':
            prompt = config.get('prompt', f"Generate engaging social post for {campaign.name}")
            platform = config.get('platform', 'instagram')
            c_type = config.get('content_type', 'post')

            res = ContentGeneratorService.generate_content(
                user=campaign.user,
                prompt=prompt,
                brand=campaign.brand,
                platform=platform,
                content_type=c_type
            )
            return {'generated_content_id': res['content_id'], 'text': res['generated_text']}

        elif step.step_type in ['schedule_post', 'publish_now']:
            caption = config.get('caption', f"Campaign post for {campaign.name}")
            platforms = config.get('platforms', ['instagram'])

            post = PublishingService.create_post(
                user=campaign.user,
                brand=campaign.brand,
                workspace=campaign.workspace,
                caption=caption,
                platforms=platforms
            )

            if step.step_type == 'publish_now':
                res = PublishingService.publish_now(post)
                return {'post_id': post.id, 'publish_result': res}
            else:
                scheduled_at = timezone.now() + timezone.timedelta(hours=1)
                PublishingService.schedule_post(post, scheduled_at)
                return {'post_id': post.id, 'scheduled_at': scheduled_at.isoformat()}

        elif step.step_type == 'analytics_sync':
            social_account = SocialAccount.objects.filter(brand=campaign.brand, is_active=True).first()
            if social_account:
                snapshot = MetricsCollector.collect_account_snapshot(social_account)
                return {'snapshot_id': snapshot.id, 'followers_count': snapshot.followers_count}
            return {'status': 'no_social_account_to_sync'}

        return {'status': 'executed', 'config': config}
