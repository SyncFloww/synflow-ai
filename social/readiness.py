import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from .meta_api import configuration as meta_configuration
from .tiktok_api import configuration as tiktok_configuration, public_approved
from rest_framework.exceptions import APIException

class SocialReadiness(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        def configured(check):
            try: check(); return True
            except APIException: return False
        return Response({
            'facebook': {'configured': configured(meta_configuration), 'messenger_requested': os.getenv('META_ENABLE_MESSENGER', 'false').lower() == 'true'},
            'tiktok': {'configured': configured(tiktok_configuration), 'public_posting_approved': public_approved(), 'media_prefix_configured': bool(os.getenv('TIKTOK_MEDIA_URL_PREFIX')),
                'comments': 'Separate TikTok API for Business connection required; not implemented in this release.',
                'inbox': 'Separate Business Messaging API approval and connection required; not implemented in this release.'},
            'scheduler': {'cadence': 'daily', 'actions_per_run': 1, 'message': 'Queued posts run on a worker check after their scheduled time. Daily cron is not precise scheduling.'}
        })
