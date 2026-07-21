import json
from django.utils.deprecation import MiddlewareMixin
from .models import ActivityLog

class ActivityLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request._body = request.body
        
    def process_response(self, request, response):
        if hasattr(request, 'user') and request.user.is_authenticated:
            # We only log modifying requests (POST, PUT, DELETE, PATCH)
            if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                path = request.path
                action = f"{request.method} {path}"
                
                details = {
                    "status_code": response.status_code,
                }
                
                # Attempt to extract workspace_id from path
                # A very basic approach for Phase 1
                workspace = None
                if 'workspaces/' in path:
                    parts = path.split('/')
                    try:
                        idx = parts.index('workspaces')
                        if len(parts) > idx + 1:
                            workspace_id = parts[idx + 1]
                            from workspaces.models import Workspace
                            workspace = Workspace.objects.filter(id=workspace_id).first()
                    except ValueError:
                        pass

                # Get IP Address
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0]
                else:
                    ip = request.META.get('REMOTE_ADDR')

                ActivityLog.objects.create(
                    user=request.user,
                    workspace=workspace,
                    action=action,
                    details=details,
                    ip_address=ip
                )
        return response
