from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from .views import HomeView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', HomeView.as_view(), name='home'),
    
    # OpenAPI Schema & Swagger UI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui-alias'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    path('api/', include('users.urls')),
    path('api/users/', include('users.urls')),
    path('api/', include('projects.urls')),
    path('api/social/', include('social.urls')),
    path('api/ai/', include('ai_agents.urls')),
    path('api/workspaces/', include('workspaces.urls')),
    path('api/invitations/', include('workspaces.urls')),

    path('api/content/', include('content.urls')),
    path('api/media/', include('media.urls')),
    path('api/scheduler/', include('scheduler.urls')),
    path('api/publishing/', include('publishing.urls')),
    path('api/analytics/', include('analytics.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/campaigns/', include('campaigns.urls')),
    path('api/approvals/', include('approvals.urls')),
    
    # API v2 Modules
    path('api/v2/', include('campaigns.urls')),
    path('api/v2/', include('automation.urls')),
    path('api/v2/', include('tasks.urls')),
    path('api/v2/', include('comments.urls')),
    path('api/v2/', include('approvals.urls')),
    path('api/v2/', include('prompt_library.urls')),
    path('api/v2/', include('content_templates.urls')),
    path('api/v2/', include('reports.urls')),
    path('api/v2/', include('recommendations.urls')),
    path('api/v2/', include('crm.urls')),
    path('api/v2/', include('finance.urls')),
    path('api/v2/', include('customer_success.urls')),
    path('api/v2/', include('hr.urls')),
    path('api/v2/', include('executives.urls')),
    path('api/v2/', include('marketplace.urls')),
    path('api/v2/', include('developer.urls')),
]
