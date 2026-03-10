from celery import shared_task
from django.utils import timezone
from ai_engine.models import AgentTask
from ai_engine.agents.social_agent import SocialMediaAgent

@shared_task(bind=True, max_retries=3)
def run_agent_task(self, task_id):
    """
    Celery task that executes an Agent action for a specific AgentTask.
    Runs asynchronously, avoiding blocking the main Django thread.
    """
    try:
        task_instance = AgentTask.objects.select_related('agent', 'agent__brand').get(id=task_id)
    except AgentTask.DoesNotExist:
        return f"Task {task_id} not found."

    # Prevent running an already completed task
    if task_instance.status in ['completed', 'failed']:
        return f"Task {task_id} already processed."

    # Mark as processing
    task_instance.status = 'processing'
    task_instance.save(update_fields=['status'])

    # 1. Initialize the correct Agent type (could be generic based on DB flag)
    # We use SocialMediaAgent here for demonstration
    agent = SocialMediaAgent(task_instance.agent)
    
    # Extract the prompt to use
    prompt_input = task_instance.input_data.get('prompt', "What should I do?")

    # 2. Execute the LangChain pipeline
    try:
        # This is where the heavy DeepSeek VRAM/CPU computation happens
        # It may take several seconds, hence why it's in a Celery queue
        result = agent.execute(prompt_input)
        
        # 3. Save the results
        task_instance.output_data = result
        task_instance.status = 'completed'
        
    except Exception as exc:
        task_instance.output_data = {'error': str(exc)}
        task_instance.status = 'failed'
        
        # Optionally retry the task if it's a network failure
        raise self.retry(exc=exc, countdown=60) # Wait 60s
        
    finally:
        task_instance.completed_at = timezone.now()
        task_instance.save(update_fields=['status', 'output_data', 'completed_at'])
        
    return f"Task {task_instance.id} finished with status: {task_instance.status}"
