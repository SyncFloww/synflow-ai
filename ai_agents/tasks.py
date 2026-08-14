from celery import shared_task
import logging
from ai_agents.services.job_service import AIJobService

logger = logging.getLogger(__name__)

@shared_task
def run_ai_job_task(job_id: str):
    logger.info(f"Executing Celery task for AI Job {job_id}")
    return AIJobService.execute_job_sync(job_id)
