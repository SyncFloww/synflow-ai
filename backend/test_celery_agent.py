import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'syncfloww.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Agent, Brand, AgentTask, SocialAccount
from core.tasks import execute_agent_task

def run_celery_test():
    print("========= CELERY AGENT TEST =========")
    
    # 1. Ensure minimal data with required user owner
    admin_user, _ = User.objects.get_or_create(username="admin", defaults={'email': 'admin@syncflow.ai'})
    brand, _ = Brand.objects.get_or_create(id=1, defaults={'name': 'Nike', 'owner': admin_user})
    social, _ = SocialAccount.objects.get_or_create(platform_name="Instagram", account_id="NikeIG", brand=brand)
    agent, _ = Agent.objects.get_or_create(name="Nike Community Manager", agent_type="engagement", brand=brand, defaults={'social_account': social})

    # 2. Create the AgentTask object
    task = AgentTask.objects.create(
        agent=agent,
        task_type="comment_reply",
        input_data={"request": "Love these new shoes, when do they release in Europe?"}
    )
    
    print(f"1. Created pending AgentTask in DB (ID: {task.id}, Status: {task.status})")

    # 3. Dispatch to Celery queue (Simulated)
    print(f"2. Dispatching task to Celery queue via .delay() (simulated)")
    execute_agent_task(task.id)
    
    # 4. Verify DB status post-queue
    task.refresh_from_db()
    
    print(f"3. Validated post-queue AgentTask DB state:")
    print(f"   Status: {task.status}")
    print(f"   Output: {task.output_data}")

if __name__ == "__main__":
    run_celery_test()
