import os
from datetime import datetime, timedelta, timezone
from django.db.models import Count
from ai_agents.models import AIJob

def daily_limit():
    try:
        return max(1, min(10000, int(os.getenv('AI_DAILY_LIMIT', '30'))))
    except ValueError:
        return 30

def day_window():
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, start + timedelta(days=1)

def usage_snapshot(workspace):
    start, reset = day_window()
    today = AIJob.objects.filter(workspace=workspace, created_at__gte=start, created_at__lt=reset)
    used = today.count()
    counts = dict(today.order_by().values_list('status').annotate(count=Count('id')).values_list('status', 'count'))
    provider = os.getenv('AI_PROVIDER', 'gemini').strip().lower()
    model = os.getenv('AI_MODEL', '') or (os.getenv('HUGGINGFACE_MODEL_DEFAULT', '') if provider == 'huggingface' else '')
    key = (os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_GENAI_API_KEY')) if provider == 'gemini' else (os.getenv('HF_TOKEN') or os.getenv('HUGGINGFACE_API_KEY')) if provider == 'huggingface' else ''
    return {'workspace': workspace.id, 'daily_limit': daily_limit(), 'used': used,
            'remaining': max(0, daily_limit() - used), 'resets_at': reset,
            'completed': counts.get('COMPLETED', 0), 'failed': counts.get('FAILED', 0),
            'in_progress': counts.get('QUEUED', 0) + counts.get('PROCESSING', 0),
            'cancelled': counts.get('CANCELLED', 0), 'ai_configured': bool(model and key)}
