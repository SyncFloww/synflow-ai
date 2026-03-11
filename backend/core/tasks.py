import json
from celery import shared_task
from django.utils import timezone
from core.models import AgentTask, Agent

# Note: We simulate the LLM output currently because get_deepseek_llm is still a stub.
# In production, we load: from core.llm_agents.agent import SyncflowAgent

@shared_task
def execute_agent_task(task_id):
    """
    Background worker that executes the entire Agent memory -> LLM -> reasoning flow.
    """
    print(f"\n[Celery Worker] Starting Task ID: {task_id}")
    
    try:
        # 1. Fetch Task
        task = AgentTask.objects.get(id=task_id)
        task.status = "running"
        task.save()
        
        # 2. Extract Data
        agent = task.agent
        brand = agent.brand
        payload = task.input_data
        user_request = payload.get("request", "")
        
        print(f" -> Assigned to Agent: {agent.name} for Brand: {brand.name}")
        print(f" -> Request: {user_request}")

        # 3. Import and Run Agent Brain (Mocking output for now to prevent massive local generations)
        # agent_engine = SyncflowAgent(DummyLLM())
        # result = agent._run(user_request, brand=brand.name)
        
        result_json = {
            "thought": f"Agent {agent.name} is looking at {user_request}",
            "action": task.task_type,
            "response": f"Generated successful content for {brand.name}."
        }

        # 4. Save completed output
        task.output_data = result_json
        task.status = "completed"
        task.save()

        print(f"[Celery Worker] Finished Task ID: {task_id} gracefully.\n")
        return result_json

    except AgentTask.DoesNotExist:
        print(f"[Celery WorkerError] Task {task_id} not found in database.")
        return {"error": "Task not found"}
    except Exception as e:
        task.status = "failed"
        task.output_data = {"error": str(e)}
        task.save()
        print(f"[Celery WorkerError] Task {task_id} failed: {e}")
        return {"error": str(e)}
