from ai_engine.models import AutomationRule, AgentTask

class RuleEvaluator:
    """
    Evaluates system events to trigger Agents via AutomationRules.
    In production, this would be called by a Celery Beat schedule or a Webhook endpoint.
    """
    
    @classmethod
    def process_mention(cls, mention_text: str):
        """
        Processes a generic 'mention' text.
        If the text triggers any rules, it launches an AgentTask.
        """
        # Find all active rules that look for mentions
        rules = AutomationRule.objects.filter(is_active=True, trigger_type='mention')
        
        tasks_created = []
        for rule in rules:
            # e.g trigger_config = {"keyword": "SyncflowAI"}
            keyword = rule.trigger_config.get("keyword", "")
            
            if keyword.lower() in mention_text.lower():
                # The rule matches, trigger a task for its agent!
                task = AgentTask.objects.create(
                    agent=rule.agent,
                    rule_triggered=rule,
                    input_data={"prompt": f"Reply to this mention: '{mention_text}'"}
                )
                tasks_created.append(task)
                
                # Hand it off to Celery
                from ai_engine.tasks import run_agent_task
                run_agent_task.delay(task.id)
                
        return tasks_created
