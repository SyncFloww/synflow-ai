from datetime import timedelta
from django.utils import timezone
from rest_framework import status, views, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from workspaces.models import Workspace
from workspaces.permissions import member_for
from .models import SocialAccount, OAuthToken, Platform, ConnectionStatus
from .providers import MockOAuthProvider

class MockConnectView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, workspace_id):
        """
        Simulates the end of an OAuth flow where we receive a code,
        exchange it for tokens, and create/update the SocialAccount.
        """
        workspace = get_object_or_404(Workspace, id=workspace_id)
        if not member_for(request.user, workspace):
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        code = request.data.get("code", "valid_code")
        platform = request.data.get("platform", Platform.MOCK)

        provider = MockOAuthProvider(platform_name=platform)
        
        try:
            token_data = provider.exchange_code_for_token(code, "http://localhost/callback")
            profile_data = provider.fetch_user_profile(token_data["access_token"])
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Create or update SocialAccount
        account, created = SocialAccount.objects.update_or_create(
            workspace=workspace,
            platform=platform,
            platform_account_id=profile_data["id"],
            defaults={
                "username": profile_data["username"],
                "profile_url": profile_data["profile_url"],
                "status": ConnectionStatus.CONNECTED,
                "connected_by": request.user,
                "metadata": profile_data.get("metadata", {})
            }
        )

        # Create or update OAuthToken
        expires_at = timezone.now() + timedelta(seconds=token_data.get("expires_in", 3600))
        OAuthToken.objects.update_or_create(
            social_account=account,
            defaults={
                "access_token": token_data["access_token"],
                "refresh_token": token_data["refresh_token"],
                "expires_at": expires_at,
                "scopes": token_data.get("scopes", [])
            }
        )

        return Response({
            "message": "Successfully connected account.",
            "account_id": account.id,
            "platform": account.platform
        }, status=status.HTTP_201_CREATED)


class SocialAccountListAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, workspace_id):
        workspace = get_object_or_404(Workspace, id=workspace_id)
        if not member_for(request.user, workspace):
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        accounts = SocialAccount.objects.filter(workspace=workspace)
        data = []
        for acc in accounts:
            is_expired = False
            if hasattr(acc, 'token'):
                is_expired = acc.token.is_expired()
                if is_expired and acc.status == ConnectionStatus.CONNECTED:
                    acc.status = ConnectionStatus.EXPIRED
                    acc.save()
            data.append({
                "id": acc.id,
                "platform": acc.platform,
                "username": acc.username,
                "status": acc.status,
                "token_expired": is_expired,
                "connected_at": acc.created_at
            })
            
        return Response(data, status=status.HTTP_200_OK)


class DisconnectView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, account_id):
        account = get_object_or_404(SocialAccount, id=account_id)
        if not member_for(request.user, account.workspace):
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        account.status = ConnectionStatus.DISCONNECTED
        account.save()
        
        # Optionally delete token
        if hasattr(account, 'token'):
            account.token.delete()
            
        return Response({"message": "Successfully disconnected account."}, status=status.HTTP_200_OK)


class AccountStatusView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, account_id):
        account = get_object_or_404(SocialAccount, id=account_id)
        if not member_for(request.user, account.workspace):
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        is_expired = False
        if hasattr(account, 'token'):
            is_expired = account.token.is_expired()
            if is_expired and account.status == ConnectionStatus.CONNECTED:
                account.status = ConnectionStatus.EXPIRED
                account.save()

        return Response({
            "id": account.id,
            "platform": account.platform,
            "username": account.username,
            "status": account.status,
            "token_expired": is_expired
        }, status=status.HTTP_200_OK)
