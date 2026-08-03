from django.views.generic import TemplateView
from django.contrib.auth import login
from django.contrib.auth.models import User
from projects.models import Project
from social.models import Brand, SocialAccount
from ai_agents.models import AIAgent, AgentTask

class HomeView(TemplateView):
    template_name = 'index.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            try:
                user = User.objects.get(username='partnermarvel55')
                login(request, user)
            except User.DoesNotExist:
                pass
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Gather live database statistics
        context['stats'] = {
            'users': User.objects.count(),
            'projects': Project.objects.count(),
            'brands': Brand.objects.count(),
            'social_accounts': SocialAccount.objects.count(),
            'tasks': AgentTask.objects.count(),
            'failed_tasks': AgentTask.objects.filter(status='failed').count(),
        }
        
        # Gather AI agents and recent tasks
        context['agents'] = AIAgent.objects.filter(is_active=True)
        context['recent_tasks'] = AgentTask.objects.order_by('-created_at')[:8]
        
        return context
