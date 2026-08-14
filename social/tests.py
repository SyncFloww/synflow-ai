from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
import time

from workspaces.models import Workspace, WorkspaceMember
from users.models import PersonalSpace
from social.models import Brand, BrandProfile, BrandKnowledge, BrandVoice, BrandGuideline, SocialAccount, OAuthToken, OAuthAuditLog
from social.security import TokenEncryptionService, OAuthStateManager
from social.services import OAuthTokenService
from social.serializers import SocialAccountSerializer
from social.providers import (
    ProviderRegistry, get_provider, list_providers,
    InstagramOAuthProvider, FacebookOAuthProvider,
    LinkedInOAuthProvider, TikTokOAuthProvider, XOAuthProvider, YouTubeOAuthProvider
)
from django.core.exceptions import ValidationError

class BrandTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(username='user1', email='user1@example.com', password='password123')
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com', password='password123')

        self.ws1 = Workspace.objects.create(name='Workspace 1', owner=self.user1, created_by=self.user1)
        WorkspaceMember.objects.create(workspace=self.ws1, user=self.user1, role='OWNER', status='ACTIVE')

        self.ws2 = Workspace.objects.create(name='Workspace 2', owner=self.user2, created_by=self.user2)
        WorkspaceMember.objects.create(workspace=self.ws2, user=self.user2, role='OWNER', status='ACTIVE')

        self.client.force_authenticate(user=self.user1)

    def test_create_brand_scoped_to_workspace(self):
        response = self.client.post('/api/social/brands/', {
            'workspace': self.ws1.id,
            'name': 'Brand Alpha',
            'industry': 'Tech',
            'voice': 'Bold'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        brand_id = response.data['id']
        brand = Brand.objects.get(id=brand_id)

        self.assertEqual(brand.workspace, self.ws1)
        self.assertTrue(BrandProfile.objects.filter(brand=brand).exists())
        self.assertTrue(BrandVoice.objects.filter(brand=brand).exists())
        self.assertTrue(BrandGuideline.objects.filter(brand=brand).exists())

    def test_brand_cross_tenant_isolation(self):
        brand = Brand.objects.create(workspace=self.ws1, created_by=self.user1, name='Alpha Brand')

        self.client.force_authenticate(user=self.user2)
        response = self.client.get('/api/social/brands/')
        self.assertEqual(len(response.data), 0)

        response = self.client.get(f'/api/social/brands/{brand.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_personal_space_endpoint(self):
        response = self.client.get('/api/me/personal-space/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Personal Space', response.data['name'])

class CryptographicSecurityAndTokenEncryptionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='sec_user', email='sec@example.com', password='password123')
        self.ws = Workspace.objects.create(name='Sec Workspace', owner=self.user, created_by=self.user)
        self.brand = Brand.objects.create(workspace=self.ws, created_by=self.user, name='Sec Brand')

    def test_token_encryption_service(self):
        raw_access = "secret_access_token_12345"
        raw_refresh = "secret_refresh_token_67890"

        encrypted_access = TokenEncryptionService.encrypt(raw_access)
        encrypted_refresh = TokenEncryptionService.encrypt(raw_refresh)

        self.assertNotEqual(raw_access, encrypted_access)
        self.assertNotEqual(raw_refresh, encrypted_refresh)

        decrypted_access = TokenEncryptionService.decrypt(encrypted_access)
        decrypted_refresh = TokenEncryptionService.decrypt(encrypted_refresh)

        self.assertEqual(raw_access, decrypted_access)
        self.assertEqual(raw_refresh, decrypted_refresh)

    def test_oauth_state_manager_crypto_and_replay_protection(self):
        signed_state, verifier = OAuthStateManager.generate_state(
            user_id=self.user.id,
            workspace_id=self.ws.id,
            brand_id=self.brand.id,
            provider='instagram'
        )

        self.assertTrue(len(signed_state) > 20)

        # Validate state
        extracted = OAuthStateManager.validate_and_consume_state(signed_state, 'instagram')
        self.assertEqual(extracted['user_id'], self.user.id)
        self.assertEqual(extracted['workspace_id'], self.ws.id)
        self.assertEqual(extracted['brand_id'], self.brand.id)

        # Single-use enforcement: second validation attempt must fail (replay protection)
        with self.assertRaises(ValueError) as ctx:
            OAuthStateManager.validate_and_consume_state(signed_state, 'instagram')
        self.assertIn('already been used', str(ctx.exception))

class SocialOAuthProductionFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(username='user1', email='user1@example.com', password='password123')
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com', password='password123')

        self.ws1 = Workspace.objects.create(name='Workspace 1', owner=self.user1, created_by=self.user1)
        WorkspaceMember.objects.create(workspace=self.ws1, user=self.user1, role='OWNER', status='ACTIVE')

        self.ws2 = Workspace.objects.create(name='Workspace 2', owner=self.user2, created_by=self.user2)
        WorkspaceMember.objects.create(workspace=self.ws2, user=self.user2, role='OWNER', status='ACTIVE')

        self.brand1 = Brand.objects.create(workspace=self.ws1, created_by=self.user1, name='Brand One')
        self.brand2 = Brand.objects.create(workspace=self.ws2, created_by=self.user2, name='Brand Two')

        self.client.force_authenticate(user=self.user1)

    def test_list_oauth_providers(self):
        res = self.client.get('/api/social/oauth/providers/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(len(res.data) >= 6)
        p_names = [p['name'] for p in res.data]
        self.assertIn('instagram', p_names)
        self.assertIn('facebook', p_names)

        # Check capabilities in provider list response
        insta_info = next(p for p in res.data if p['name'] == 'instagram')
        self.assertIn('capabilities', insta_info)
        self.assertIn('scopes', insta_info)

    def test_oauth_authorize_flow(self):
        res = self.client.get(f'/api/social/oauth/authorize/?provider=instagram&account_type=brand&brand_id={self.brand1.id}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('authorization_url', res.data)
        self.assertIn('state', res.data)
        self.assertIn('capabilities', res.data)
        self.assertEqual(res.data['brand_id'], self.brand1.id)

        # Confirm audit log created
        self.assertTrue(OAuthAuditLog.objects.filter(action='OAUTH_INITIATED', user=self.user1).exists())

        # Cross-tenant attempt denied for User 1 on Brand 2
        res_cross = self.client.get(f'/api/social/oauth/authorize/?provider=instagram&account_type=brand&brand_id={self.brand2.id}')
        self.assertEqual(res_cross.status_code, status.HTTP_403_FORBIDDEN)

    def test_mock_oauth_callback_flow(self):
        res_auth = self.client.get(f'/api/social/oauth/authorize/?provider=instagram&account_type=brand&brand_id={self.brand1.id}')
        state = res_auth.data['state']
        auth_url = res_auth.data['authorization_url']
        code = auth_url.split('code=')[1].split('&')[0]

        res_cb = self.client.post('/api/social/oauth/callback/', {
            'provider': 'instagram',
            'code': code,
            'state': state
        })

        self.assertEqual(res_cb.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_cb.data['brand'], self.brand1.id)
        self.assertEqual(res_cb.data['status'], 'ACTIVE')

        acc_id = res_cb.data['id']
        account = SocialAccount.objects.get(id=acc_id)

        # Verify tokens are encrypted
        token_obj = OAuthToken.objects.get(social_account=account)
        self.assertNotEqual(token_obj.encrypted_access_token, token_obj.access_token)
        self.assertTrue(token_obj.access_token.startswith('mock_access_tok_'))

        # Verify audit log
        self.assertTrue(OAuthAuditLog.objects.filter(action='OAUTH_SUCCESS', brand=self.brand1).exists())

    def test_social_account_verify_and_disconnect(self):
        acc = SocialAccount.objects.create(
            brand=self.brand1,
            connected_by=self.user1,
            platform='instagram',
            username='brand1_insta',
            account_id='123456',
            status='ACTIVE',
            is_active=True
        )
        OAuthTokenService.store_tokens(
            social_account=acc,
            access_token='mock_access_tok_insta',
            refresh_token='mock_refresh_tok_insta'
        )

        # Test verification API
        res_verify = self.client.post(f'/api/social/accounts/{acc.id}/verify/')
        self.assertEqual(res_verify.status_code, status.HTTP_200_OK)
        self.assertTrue(res_verify.data['is_valid'])

        # Test disconnect API
        res_disc = self.client.post(f'/api/social/accounts/{acc.id}/disconnect/')
        self.assertEqual(res_disc.status_code, status.HTTP_200_OK)

        acc.refresh_from_db()
        self.assertEqual(acc.status, 'DISCONNECTED')
        self.assertFalse(acc.is_active)
        self.assertFalse(OAuthToken.objects.filter(social_account=acc).exists())
        self.assertTrue(OAuthAuditLog.objects.filter(action='DISCONNECTED', brand=self.brand1).exists())
