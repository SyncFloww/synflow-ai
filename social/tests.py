from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from workspaces.models import Workspace, WorkspaceMember
from users.models import PersonalSpace
from social.models import Brand, BrandProfile, BrandKnowledge, BrandVoice, BrandGuideline, SocialAccount, OAuthToken
from social.providers import MockSocialProvider, get_provider

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
        # Create brand in ws1
        brand = Brand.objects.create(workspace=self.ws1, created_by=self.user1, name='Alpha Brand')

        # User 2 cannot see or access brand
        self.client.force_authenticate(user=self.user2)
        response = self.client.get('/api/social/brands/')
        self.assertEqual(len(response.data), 0)

        response = self.client.get(f'/api/social/brands/{brand.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # User 2 cannot create brand in User 1's workspace
        response = self.client.post('/api/social/brands/', {
            'workspace': self.ws1.id,
            'name': 'Unauthorized Brand'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_brand_profile_and_knowledge_apis(self):
        brand = Brand.objects.create(workspace=self.ws1, created_by=self.user1, name='Beta Brand')

        # Test profile GET and PATCH
        response = self.client.get(f'/api/social/brands/{brand.id}/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.patch(f'/api/social/brands/{brand.id}/profile/', {
            'tagline': 'Building the future',
            'mission': 'Empower creators'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['tagline'], 'Building the future')

        # Test knowledge items
        response = self.client.post(f'/api/social/brands/{brand.id}/knowledge/', {
            'title': 'Company Overview',
            'content': 'We are an AI company.',
            'knowledge_type': 'ABOUT'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(f'/api/social/brands/{brand.id}/knowledge/')
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Company Overview')

    def test_personal_space_endpoint(self):
        response = self.client.get('/api/me/personal-space/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Personal Space', response.data['name'])

    def test_full_cross_tenant_brand_profile_knowledge_social_isolation(self):
        # Create Brand B in Workspace 2 owned by User 2
        brand_b = Brand.objects.create(workspace=self.ws2, created_by=self.user2, name='Brand Beta')
        profile_b, _ = BrandProfile.objects.get_or_create(brand=brand_b)
        knowledge_b = BrandKnowledge.objects.create(brand=brand_b, title='Secret B', content='Private Info', knowledge_type='ABOUT')

        # User 1 attempts to access Brand B resources
        self.client.force_authenticate(user=self.user1)

        # Cannot GET / PATCH / DELETE Brand B
        self.assertEqual(self.client.get(f'/api/social/brands/{brand_b.id}/').status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.patch(f'/api/social/brands/{brand_b.id}/', {'name': 'Hacked'}).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.delete(f'/api/social/brands/{brand_b.id}/').status_code, status.HTTP_404_NOT_FOUND)

        # Cannot GET / PATCH Brand B Profile via brand endpoint
        self.assertEqual(self.client.get(f'/api/social/brands/{brand_b.id}/profile/').status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.patch(f'/api/social/brands/{brand_b.id}/profile/', {'tagline': 'Hacked'}).status_code, status.HTTP_404_NOT_FOUND)

        # Cannot GET / PATCH Brand B Profile via direct brand-profiles ViewSet
        self.assertEqual(self.client.get(f'/api/social/brand-profiles/{profile_b.id}/').status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.patch(f'/api/social/brand-profiles/{profile_b.id}/', {'tagline': 'Hacked'}).status_code, status.HTTP_404_NOT_FOUND)

        # Cannot GET / POST Brand B Knowledge via brand endpoint
        self.assertEqual(self.client.get(f'/api/social/brands/{brand_b.id}/knowledge/').status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.post(f'/api/social/brands/{brand_b.id}/knowledge/', {'title': 'Hack', 'content': 'Hack'}).status_code, status.HTTP_404_NOT_FOUND)

        # Cannot GET / PATCH Brand B Knowledge via direct knowledge ViewSet
        self.assertEqual(self.client.get(f'/api/social/knowledge/{knowledge_b.id}/').status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.patch(f'/api/social/knowledge/{knowledge_b.id}/', {'title': 'Hack'}).status_code, status.HTTP_404_NOT_FOUND)

        # Cannot attach Brand B (from Workspace 2) when connecting social account
        connect_res = self.client.post('/api/social/connect/youtube/', {'username': 'user1_yt', 'brand_id': brand_b.id}, format='json')
        self.assertEqual(connect_res.status_code, status.HTTP_404_NOT_FOUND)

class Milestone3OAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(username='user1', email='user1@example.com', password='password123')
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com', password='password123')

        self.ps1, _ = PersonalSpace.objects.get_or_create(user=self.user1)
        self.ps2, _ = PersonalSpace.objects.get_or_create(user=self.user2)

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
        provider_names = [p['name'] for p in res.data]
        self.assertIn('instagram', provider_names)
        self.assertIn('youtube', provider_names)

    def test_oauth_authorize_flow(self):
        # Personal space authorize
        res = self.client.get('/api/social/oauth/authorize/?provider=instagram&account_type=personal')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('authorization_url', res.data)
        self.assertIn('code=', res.data['authorization_url'])

        # Brand space authorize
        res = self.client.get(f'/api/social/oauth/authorize/?provider=instagram&account_type=brand&brand_id={self.brand1.id}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('authorization_url', res.data)

        # Cross-tenant brand space authorize denied for User 1 on Brand 2
        res = self.client.get(f'/api/social/oauth/authorize/?provider=instagram&account_type=brand&brand_id={self.brand2.id}')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_mock_oauth_callback_connect_personal_and_brand_account(self):
        # Connect Personal Social Account via Mock OAuth Callback
        res_auth = self.client.get('/api/social/oauth/authorize/?provider=instagram&account_type=personal')
        auth_url = res_auth.data['authorization_url']
        # Extract code
        code = auth_url.split('code=')[1].split('&')[0]

        res_cb = self.client.post('/api/social/oauth/callback/', {
            'provider': 'instagram',
            'code': code,
            'account_type': 'personal'
        })
        self.assertEqual(res_cb.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_cb.data['personal_space'], self.ps1.id)
        self.assertIsNone(res_cb.data['brand'])

        account_id = res_cb.data['id']
        account = SocialAccount.objects.get(id=account_id)
        self.assertTrue(hasattr(account, 'oauth_token'))
        self.assertTrue(account.oauth_token.access_token.startswith('mock_access_tok_'))

        # Cannot reuse code
        res_reuse = self.client.post('/api/social/oauth/callback/', {
            'provider': 'instagram',
            'code': code,
            'account_type': 'personal'
        })
        self.assertEqual(res_reuse.status_code, status.HTTP_400_BAD_REQUEST)

        # Connect Brand Social Account via Mock OAuth Callback
        res_auth_brand = self.client.get(f'/api/social/oauth/authorize/?provider=youtube&account_type=brand&brand_id={self.brand1.id}')
        brand_code = res_auth_brand.data['authorization_url'].split('code=')[1].split('&')[0]

        res_cb_brand = self.client.post('/api/social/oauth/callback/', {
            'provider': 'youtube',
            'code': brand_code,
            'account_type': 'brand',
            'brand_id': self.brand1.id
        })
        self.assertEqual(res_cb_brand.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_cb_brand.data['brand'], self.brand1.id)

    def test_social_account_token_refresh_and_disconnect(self):
        # Create a personal account with OAuth token
        acc = SocialAccount.objects.create(
            personal_space=self.ps1,
            connected_by=self.user1,
            platform='linkedin',
            username='user1_linkedin',
            display_name='User1 LinkedIn',
            is_active=True
        )
        token_obj = OAuthToken.objects.create(
            social_account=acc,
            access_token='old_access_token',
            refresh_token='old_refresh_token',
            expires_at=timezone.now() - timedelta(days=1)
        )

        # Test refresh endpoint
        res = self.client.post(f'/api/social/accounts/{acc.id}/refresh/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        token_obj.refresh_from_db()
        self.assertTrue('refreshed' in token_obj.access_token)

        # Test disconnect endpoint
        res_disc = self.client.post(f'/api/social/accounts/{acc.id}/disconnect/')
        self.assertEqual(res_disc.status_code, status.HTTP_200_OK)
        self.assertFalse(SocialAccount.objects.filter(id=acc.id).exists())

    def test_cross_tenant_social_account_isolation(self):
        # User 2 creates personal social account
        acc_user2 = SocialAccount.objects.create(
            personal_space=self.ps2,
            connected_by=self.user2,
            platform='twitter',
            username='user2_twitter',
            display_name='User2 Twitter'
        )

        # User 1 attempts to list / access / refresh / disconnect User 2's account
        self.client.force_authenticate(user=self.user1)

        # List should not contain User 2's personal account
        res_list = self.client.get('/api/social/accounts/')
        account_ids = [a['id'] for a in res_list.data]
        self.assertNotIn(acc_user2.id, account_ids)

        # Retrieve should be 404
        self.assertEqual(self.client.get(f'/api/social/accounts/{acc_user2.id}/').status_code, status.HTTP_404_NOT_FOUND)

        # Refresh should be 404
        self.assertEqual(self.client.post(f'/api/social/accounts/{acc_user2.id}/refresh/').status_code, status.HTTP_404_NOT_FOUND)

        # Disconnect should be 404
        self.assertEqual(self.client.post(f'/api/social/accounts/{acc_user2.id}/disconnect/').status_code, status.HTTP_404_NOT_FOUND)

from social.services import OAuthTokenService
from social.serializers import SocialAccountSerializer
from social.providers import (
    ProviderRegistry, get_provider, list_providers,
    InstagramOAuthProvider, FacebookOAuthProvider,
    LinkedInOAuthProvider, TikTokOAuthProvider, XOAuthProvider
)
from django.core.exceptions import ValidationError

class SocialAccountTenancyAndTokenServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.ps, _ = PersonalSpace.objects.get_or_create(user=self.user)
        self.ws = Workspace.objects.create(name='Test Workspace', owner=self.user, created_by=self.user)
        self.brand = Brand.objects.create(workspace=self.ws, created_by=self.user, name='Test Brand')

    def test_tenancy_boundary_isolation(self):
        # Personal Space account
        ps_acc = SocialAccount.objects.create(
            personal_space=self.ps,
            connected_by=self.user,
            platform='instagram',
            username='ps_insta'
        )
        self.assertEqual(ps_acc.owner_type, 'personal_space')
        self.assertEqual(ps_acc.owner_id, self.ps.id)
        self.assertIsNone(ps_acc.brand)

        # Brand account
        brand_acc = SocialAccount.objects.create(
            brand=self.brand,
            connected_by=self.user,
            platform='facebook',
            username='brand_fb'
        )
        self.assertEqual(brand_acc.owner_type, 'brand')
        self.assertEqual(brand_acc.owner_id, self.brand.id)
        self.assertEqual(brand_acc.owner_name, 'Test Brand')
        self.assertIsNone(brand_acc.personal_space)

        # Disallow dual ownership
        with self.assertRaises(ValidationError):
            SocialAccount.objects.create(
                personal_space=self.ps,
                brand=self.brand,
                connected_by=self.user,
                platform='linkedin',
                username='dual_user'
            )

    def test_oauth_token_service_isolation_and_security(self):
        acc = SocialAccount.objects.create(
            personal_space=self.ps,
            connected_by=self.user,
            platform='tiktok',
            username='tt_user'
        )

        # Store tokens via service
        OAuthTokenService.store_tokens(
            social_account=acc,
            access_token='sec_access_123',
            refresh_token='sec_refresh_456',
            expires_at=timezone.now() + timedelta(days=1)
        )

        # Backend retrieval works
        tokens = OAuthTokenService.get_tokens(acc)
        self.assertEqual(tokens['access_token'], 'sec_access_123')
        self.assertEqual(tokens['refresh_token'], 'sec_refresh_456')

        # Valid access token retrieval
        valid_token = OAuthTokenService.get_valid_access_token(acc)
        self.assertEqual(valid_token, 'sec_access_123')

        # Serializer check: response does not expose token string
        serializer = SocialAccountSerializer(acc)
        data = serializer.data
        self.assertNotIn('access_token', data)
        self.assertNotIn('access_token', data.get('oauth_token_detail', {}))
        self.assertNotIn('refresh_token', data.get('oauth_token_detail', {}))

        # Token revocation and deletion
        revoked = OAuthTokenService.revoke_and_delete_tokens(acc)
        self.assertTrue(revoked)
        self.assertIsNone(OAuthTokenService.get_tokens(acc))

class OAuthProviderRegistryTests(TestCase):
    def test_provider_registry_lookup(self):
        providers = ['instagram', 'facebook', 'linkedin', 'tiktok', 'x', 'twitter']
        for p_name in providers:
            provider = get_provider(p_name)
            self.assertIsNotNone(provider)
            auth_url = provider.get_authorization_url(redirect_uri='http://localhost/callback', state='xyz')
            self.assertIn('http', auth_url)

        listed = list_providers()
        names = [p['name'] for p in listed]
        for expected in ['instagram', 'facebook', 'linkedin', 'tiktok', 'x']:
            self.assertIn(expected, names)
