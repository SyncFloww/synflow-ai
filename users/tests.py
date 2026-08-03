import hashlib
from datetime import timedelta
from unittest.mock import patch
from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from users.models import EmailVerification, PasswordReset, Profile, UserDevice


class RegistrationTests(APITestCase):
    def test_valid_registration(self):
        url = reverse('register')
        data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'StrongPassword123!',
            'password_confirmation': 'StrongPassword123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['email'], 'testuser@example.com')
        self.assertEqual(response.data['user']['first_name'], 'Test')
        self.assertNotIn('password', response.data['user'])
        self.assertTrue(User.objects.filter(email='testuser@example.com').exists())

        # Verify code in DB is sha256 hashed (64 chars)
        verif = EmailVerification.objects.filter(user__email='testuser@example.com').first()
        self.assertIsNotNone(verif)
        self.assertEqual(len(verif.code), 64)

    def test_duplicate_email(self):
        User.objects.create_user(username='existing', email='existing@example.com', password='Password123!')
        url = reverse('register')
        data = {
            'username': 'newuser',
            'email': 'existing@example.com',
            'password': 'StrongPassword123!',
            'password_confirmation': 'StrongPassword123!'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_duplicate_username(self):
        User.objects.create_user(username='takenuser', email='first@example.com', password='Password123!')
        url = reverse('register')
        data = {
            'username': 'takenuser',
            'email': 'second@example.com',
            'password': 'StrongPassword123!',
            'password_confirmation': 'StrongPassword123!'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_mismatch(self):
        url = reverse('register')
        data = {
            'username': 'mismatch',
            'email': 'mismatch@example.com',
            'password': 'StrongPassword123!',
            'password_confirmation': 'DifferentPassword123!'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_weak_password(self):
        url = reverse('register')
        data = {
            'username': 'weakpass',
            'email': 'weakpass@example.com',
            'password': '123',
            'password_confirmation': '123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_required_fields(self):
        url = reverse('register')
        response = self.client.post(url, {'email': 'incomplete@example.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EmailVerificationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='verifuser', email='verif@example.com', password='Password123!')
        self.profile, _ = Profile.objects.get_or_create(user=self.user, defaults={'email_confirmed': False})

    def test_verification_succeeds(self):
        raw_code = '123456'
        hashed_code = hashlib.sha256(raw_code.encode()).hexdigest()
        verif = EmailVerification.objects.create(
            user=self.user,
            code=hashed_code,
            expires_at=timezone.now() + timedelta(hours=1)
        )
        url = reverse('verify_email')
        response = self.client.post(url, {'email': 'verif@example.com', 'code': raw_code}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.email_confirmed)

        verif.refresh_from_db()
        self.assertTrue(verif.is_verified)

    def test_verification_attempt_limit_exceeded(self):
        raw_code = '123456'
        hashed_code = hashlib.sha256(raw_code.encode()).hexdigest()
        verif = EmailVerification.objects.create(
            user=self.user,
            code=hashed_code,
            expires_at=timezone.now() + timedelta(hours=1)
        )
        url = reverse('verify_email')

        # Send 4 wrong attempts
        for _ in range(4):
            response = self.client.post(url, {'email': 'verif@example.com', 'code': '000000'}, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 5th attempt should exceed maximum verification attempts limit
        response = self.client.post(url, {'email': 'verif@example.com', 'code': '000000'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Maximum verification attempts', response.data['error'])

        verif.refresh_from_db()
        self.assertTrue(verif.is_verified)  # Challenge invalidated

        # Further attempts rejected even if raw code is correct
        response_correct = self.client.post(url, {'email': 'verif@example.com', 'code': raw_code}, format='json')
        self.assertEqual(response_correct.status_code, status.HTTP_400_BAD_REQUEST)

    def test_used_verification_rejected(self):
        raw_code = '123456'
        hashed_code = hashlib.sha256(raw_code.encode()).hexdigest()
        EmailVerification.objects.create(
            user=self.user,
            code=hashed_code,
            is_verified=True,
            expires_at=timezone.now() + timedelta(hours=1)
        )
        url = reverse('verify_email')
        response = self.client.post(url, {'email': 'verif@example.com', 'code': raw_code}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_token_rejected(self):
        url = reverse('verify_email')
        response = self.client.post(url, {'email': 'verif@example.com', 'code': '999999'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_expired_token_rejected(self):
        raw_code = '123456'
        hashed_code = hashlib.sha256(raw_code.encode()).hexdigest()
        EmailVerification.objects.create(
            user=self.user,
            code=hashed_code,
            expires_at=timezone.now() - timedelta(hours=1)
        )
        url = reverse('verify_email')
        response = self.client.post(url, {'email': 'verif@example.com', 'code': raw_code}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_resend_verification_invalidates_previous_codes(self):
        raw_code = '111111'
        hashed_code = hashlib.sha256(raw_code.encode()).hexdigest()
        old_verif = EmailVerification.objects.create(
            user=self.user,
            code=hashed_code,
            expires_at=timezone.now() + timedelta(hours=1)
        )
        EmailVerification.objects.filter(id=old_verif.id).update(created_at=timezone.now() - timedelta(seconds=120))
        url = reverse('resend_verification')
        response = self.client.post(url, {'email': 'verif@example.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        old_verif.refresh_from_db()
        self.assertTrue(old_verif.is_verified) # Previous challenge invalidated

        new_verif = EmailVerification.objects.filter(user=self.user, is_verified=False).first()
        self.assertIsNotNone(new_verif)
        self.assertNotEqual(new_verif.code, hashed_code)

    def test_resend_verification_rate_limiting(self):
        raw_code = '111111'
        hashed_code = hashlib.sha256(raw_code.encode()).hexdigest()
        EmailVerification.objects.create(
            user=self.user,
            code=hashed_code,
            created_at=timezone.now(),
            expires_at=timezone.now() + timedelta(hours=1)
        )
        url = reverse('reverse_email' if False else 'resend_verification')
        response = self.client.post(url, {'email': 'verif@example.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_plaintext_code_in_db_rejected(self):
        # Raw plaintext code in DB must NOT match submitted raw code
        raw_code = '123456'
        EmailVerification.objects.create(
            user=self.user,
            code=raw_code,
            expires_at=timezone.now() + timedelta(hours=1)
        )
        url = reverse('verify_email')
        response = self.client.post(url, {'email': 'verif@example.com', 'code': raw_code}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sixth_attempt_cannot_succeed(self):
        raw_code = '123456'
        hashed_code = hashlib.sha256(raw_code.encode()).hexdigest()
        verif = EmailVerification.objects.create(
            user=self.user,
            code=hashed_code,
            expires_at=timezone.now() + timedelta(hours=1)
        )
        url = reverse('verify_email')

        # 5 failed attempts
        for _ in range(5):
            self.client.post(url, {'email': 'verif@example.com', 'code': '000000'}, format='json')

        verif.refresh_from_db()
        self.assertTrue(verif.is_verified)  # Challenge invalidated

        # 6th attempt with correct raw code fails
        response = self.client.post(url, {'email': 'verif@example.com', 'code': raw_code}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='loginuser', email='login@example.com', password='Password123!')

    def test_valid_login_by_email(self):
        url = reverse('login')
        response = self.client.post(url, {'email': 'login@example.com', 'password': 'Password123!'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_valid_login_by_username(self):
        url = reverse('login')
        response = self.client.post(url, {'username': 'loginuser', 'password': 'Password123!'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_password(self):
        url = reverse('login')
        response = self.client.post(url, {'email': 'login@example.com', 'password': 'WrongPassword!'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_nonexistent_user(self):
        url = reverse('login')
        response = self.client.post(url, {'email': 'nobody@example.com', 'password': 'Password123!'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_disabled_user(self):
        self.user.is_active = False
        self.user.save()
        url = reverse('login')
        response = self.client.post(url, {'email': 'login@example.com', 'password': 'Password123!'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_device_tracking(self):
        url = reverse('login')
        data = {
            'email': 'login@example.com',
            'password': 'Password123!',
            'device_type': 'mobile',
            'device_token': 'fcm_token_123'
        }
        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(UserDevice.objects.filter(user=self.user, device_type='mobile', device_token='fcm_token_123').exists())


class JwtAndLogoutTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='jwtuser', email='jwt@example.com', password='Password123!')
        login_url = reverse('login')
        res = self.client.post(login_url, {'email': 'jwt@example.com', 'password': 'Password123!'}, format='json')
        self.access = res.data['access']
        self.refresh = res.data['refresh']

    def test_access_token_protects_me_endpoint(self):
        url = reverse('me')
        res = self.client.get(url)
        self.assertIn(res.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access}')
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['email'], 'jwt@example.com')

    def test_token_refresh(self):
        url = reverse('token_refresh')
        res = self.client.post(url, {'refresh': self.refresh}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)

    def test_token_refresh_rotation_and_blacklisting(self):
        url = reverse('token_refresh')
        res = self.client.post(url, {'refresh': self.refresh}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_refresh = res.data['refresh']

        res_old = self.client.post(url, {'refresh': self.refresh}, format='json')
        self.assertEqual(res_old.status_code, status.HTTP_401_UNAUTHORIZED)

        res_new = self.client.post(url, {'refresh': new_refresh}, format='json')
        self.assertEqual(res_new.status_code, status.HTTP_200_OK)

    def test_logout_blacklists_refresh_token(self):
        logout_url = reverse('logout')
        refresh_url = reverse('token_refresh')

        res = self.client.post(logout_url, {'refresh': self.refresh}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        res = self.client.post(refresh_url, {'refresh': self.refresh}, format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_missing_or_invalid_refresh_token(self):
        logout_url = reverse('logout')

        res_missing = self.client.post(logout_url, {}, format='json')
        self.assertEqual(res_missing.status_code, status.HTTP_400_BAD_REQUEST)

        res_invalid = self.client.post(logout_url, {'refresh': 'invalid.token.here'}, format='json')
        self.assertEqual(res_invalid.status_code, status.HTTP_400_BAD_REQUEST)


class PasswordManagementTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='passuser', email='pass@example.com', password='OldPassword123!')

    def test_change_password_success(self):
        login_res = self.client.post(reverse('login'), {'email': 'pass@example.com', 'password': 'OldPassword123!'}, format='json')
        access = login_res.data['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        url = reverse('change_password')
        res = self.client.post(url, {
            'old_password': 'OldPassword123!',
            'new_password': 'NewStrongPassword123!',
            'new_password_confirmation': 'NewStrongPassword123!'
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        old_login = self.client.post(reverse('login'), {'email': 'pass@example.com', 'password': 'OldPassword123!'}, format='json')
        self.assertEqual(old_login.status_code, status.HTTP_401_UNAUTHORIZED)

        new_login = self.client.post(reverse('login'), {'email': 'pass@example.com', 'password': 'NewStrongPassword123!'}, format='json')
        self.assertEqual(new_login.status_code, status.HTTP_200_OK)

    def test_change_password_invalidates_refresh_tokens(self):
        login_res = self.client.post(reverse('login'), {'email': 'pass@example.com', 'password': 'OldPassword123!'}, format='json')
        access = login_res.data['access']
        refresh = login_res.data['refresh']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        url = reverse('change_password')
        res = self.client.post(url, {
            'old_password': 'OldPassword123!',
            'new_password': 'NewStrongPassword123!',
            'new_password_confirmation': 'NewStrongPassword123!'
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Confirm old refresh token is invalidated
        refresh_url = reverse('token_refresh')
        ref_res = self.client.post(refresh_url, {'refresh': refresh}, format='json')
        self.assertEqual(ref_res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password_incorrect_old(self):
        login_res = self.client.post(reverse('login'), {'email': 'pass@example.com', 'password': 'OldPassword123!'}, format='json')
        access = login_res.data['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        url = reverse('change_password')
        res = self.client.post(url, {
            'old_password': 'WrongOldPassword!',
            'new_password': 'NewStrongPassword123!',
            'new_password_confirmation': 'NewStrongPassword123!'
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_request_and_confirm(self):
        login_res = self.client.post(reverse('login'), {'email': 'pass@example.com', 'password': 'OldPassword123!'}, format='json')
        old_refresh = login_res.data['refresh']

        reset_url = reverse('password_reset')
        res = self.client.post(reset_url, {'email': 'pass@example.com'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Retrieve raw token from email outbox
        self.assertTrue(len(mail.outbox) > 0)
        email_body = mail.outbox[-1].body
        raw_token = email_body.split('token: ')[1].strip()

        # Retrieve generated token from DB and confirm it is hashed
        reset_obj = PasswordReset.objects.filter(user=self.user, is_used=False).first()
        self.assertIsNotNone(reset_obj)
        self.assertEqual(len(reset_obj.token), 64)

        confirm_url = reverse('password_reset_confirm')
        res = self.client.post(confirm_url, {
            'token': raw_token,
            'new_password': 'ResetPassword123!',
            'new_password_confirmation': 'ResetPassword123!'
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Confirm old refresh token is invalidated by password reset
        refresh_url = reverse('token_refresh')
        ref_res = self.client.post(refresh_url, {'refresh': old_refresh}, format='json')
        self.assertEqual(ref_res.status_code, status.HTTP_401_UNAUTHORIZED)

        login_res = self.client.post(reverse('login'), {'email': 'pass@example.com', 'password': 'ResetPassword123!'}, format='json')
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)


class GoogleAuthTests(APITestCase):
    def test_google_auth_new_user_in_test_mode(self):
        url = reverse('google_auth')
        data = {
            'token': 'test_google_token_123',
            'email': 'newgoogle@example.com',
            'first_name': 'Google',
            'last_name': 'User'
        }
        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)
        self.assertEqual(res.data['user']['email'], 'newgoogle@example.com')
        self.assertTrue(User.objects.filter(email='newgoogle@example.com').exists())

    def test_google_auth_existing_user(self):
        User.objects.create_user(username='existinggoogle@example.com', email='existinggoogle@example.com', password='Password123!')
        url = reverse('google_auth')
        data = {
            'token': 'test_google_token_456',
            'email': 'existinggoogle@example.com'
        }
        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['created'], False)

    @patch('users.views.settings.TESTING', False)
    def test_google_auth_mock_disabled_in_production(self):
        url = reverse('google_auth')
        data = {
            'token': 'test_google_token_123',
            'email': 'mockprod@example.com'
        }
        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('disabled in production', res.data['error'])

    @patch('users.views.settings.TESTING', False)
    @patch('google.oauth2.id_token.verify_oauth2_token')
    def test_google_auth_safe_error_handling(self, mock_verify):
        mock_verify.side_effect = Exception('Internal OAuth verification failed details')
        url = reverse('google_auth')
        data = {'token': 'real_format_google_token_999'}
        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data['error'], 'Invalid Google credential.')

    @patch('google.oauth2.id_token.verify_oauth2_token')
    def test_google_auth_unverified_email_rejected(self, mock_verify):
        mock_verify.return_value = {
            'email': 'unverified@example.com',
            'email_verified': False,
            'given_name': 'Unverified',
            'family_name': 'User'
        }
        url = reverse('google_auth')
        data = {'token': 'valid_google_id_token'}
        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('not verified', res.data['error'])


class ProfileAndAccountDeletionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='profileuser', email='profile@example.com', password='Password123!', first_name='Profile', last_name='User')
        self.profile, _ = Profile.objects.get_or_create(user=self.user, defaults={'full_name': 'Profile User'})

    def test_get_and_update_profile(self):
        login_res = self.client.post(reverse('login'), {'email': 'profile@example.com', 'password': 'Password123!'}, format='json')
        access = login_res.data['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        me_url = reverse('me')

        res_get = self.client.get(me_url)
        self.assertEqual(res_get.status_code, status.HTTP_200_OK)
        self.assertEqual(res_get.data['email'], 'profile@example.com')

        res_patch = self.client.patch(me_url, {'first_name': 'UpdatedFirst', 'full_name': 'Updated Full Name'}, format='json')
        self.assertEqual(res_patch.status_code, status.HTTP_200_OK)
        self.assertEqual(res_patch.data['first_name'], 'UpdatedFirst')
        self.assertEqual(res_patch.data['profile']['full_name'], 'Updated Full Name')

    def test_delete_account_with_password(self):
        login_res = self.client.post(reverse('login'), {'email': 'profile@example.com', 'password': 'Password123!'}, format='json')
        access = login_res.data['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        delete_url = reverse('delete_account')

        res_fail = self.client.delete(delete_url, {'password': 'WrongPassword'}, format='json')
        self.assertEqual(res_fail.status_code, status.HTTP_400_BAD_REQUEST)

        res_ok = self.client.delete(delete_url, {'password': 'Password123!'}, format='json')
        self.assertEqual(res_ok.status_code, status.HTTP_200_OK)
        self.assertFalse(User.objects.filter(email='profile@example.com').exists())


class SecurityRegressionTests(APITestCase):
    def test_sensitive_fields_never_serialized(self):
        user = User.objects.create_user(username='secuser', email='sec@example.com', password='SuperSecretPassword123!')
        login_res = self.client.post(reverse('login'), {'email': 'sec@example.com', 'password': 'SuperSecretPassword123!'}, format='json')
        access = login_res.data['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        me_res = self.client.get(reverse('me'))

        data_str = str(me_res.data)
        self.assertNotIn('password', me_res.data)
        self.assertNotIn('password_hash', data_str)
        self.assertNotIn('SuperSecretPassword123!', data_str)

    def test_protected_endpoints_reject_unauthenticated(self):
        protected_urls = [
            reverse('me'),
            reverse('change_password'),
            reverse('delete_account'),
        ]
        for url in protected_urls:
            res = self.client.get(url) if url == reverse('me') else self.client.post(url, {})
            self.assertIn(res.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class EndToEndIdentityIntegrationTest(APITestCase):
    def test_complete_identity_lifecycle(self):
        # 1. Register
        reg_url = reverse('register')
        reg_data = {
            'username': 'e2euser',
            'email': 'e2e@example.com',
            'password': 'InitialPassword123!',
            'password_confirmation': 'InitialPassword123!',
            'first_name': 'EndToEnd',
            'last_name': 'Tester'
        }
        reg_res = self.client.post(reg_url, reg_data, format='json')
        self.assertEqual(reg_res.status_code, status.HTTP_201_CREATED)

        email_body = mail.outbox[-1].body
        raw_code = email_body.split('code is: ')[1].strip()

        # 2. Verify Email
        verif_url = reverse('verify_email')
        verif_res = self.client.post(verif_url, {'email': 'e2e@example.com', 'code': raw_code}, format='json')
        self.assertEqual(verif_res.status_code, status.HTTP_200_OK)

        # 3. Login
        login_url = reverse('login')
        login_res = self.client.post(login_url, {'email': 'e2e@example.com', 'password': 'InitialPassword123!'}, format='json')
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
        access_token = login_res.data['access']
        refresh_token = login_res.data['refresh']

        # 4. Call /me
        me_url = reverse('me')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        me_res = self.client.get(me_url)
        self.assertEqual(me_res.status_code, status.HTTP_200_OK)
        self.assertEqual(me_res.data['email'], 'e2e@example.com')

        # 5. Refresh Token
        refresh_url = reverse('token_refresh')
        refresh_res = self.client.post(refresh_url, {'refresh': refresh_token}, format='json')
        self.assertEqual(refresh_res.status_code, status.HTTP_200_OK)
        new_access = refresh_res.data['access']
        new_refresh = refresh_res.data['refresh']

        # 6. Change Password
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_access}')
        change_pass_url = reverse('change_password')
        change_res = self.client.post(change_pass_url, {
            'old_password': 'InitialPassword123!',
            'new_password': 'NewE2EPassword123!',
            'new_password_confirmation': 'NewE2EPassword123!'
        }, format='json')
        self.assertEqual(change_res.status_code, status.HTTP_200_OK)

        # 7. Login with New Password
        new_login_res = self.client.post(login_url, {'email': 'e2e@example.com', 'password': 'NewE2EPassword123!'}, format='json')
        self.assertEqual(new_login_res.status_code, status.HTTP_200_OK)
        final_refresh = new_login_res.data['refresh']

        # 8. Logout
        logout_url = reverse('logout')
        logout_res = self.client.post(logout_url, {'refresh': final_refresh}, format='json')
        self.assertEqual(logout_res.status_code, status.HTTP_200_OK)

        # 9. Confirm Refresh Rejected
        revoked_refresh_res = self.client.post(refresh_url, {'refresh': final_refresh}, format='json')
        self.assertEqual(revoked_refresh_res.status_code, status.HTTP_401_UNAUTHORIZED)


class ConfigurationAndSettingsTests(APITestCase):
    def test_jwt_configuration(self):
        self.assertEqual(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'], timedelta(minutes=15))
        self.assertEqual(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'], timedelta(days=7))
        self.assertTrue(settings.SIMPLE_JWT['ROTATE_REFRESH_TOKENS'])
        self.assertTrue(settings.SIMPLE_JWT['BLACKLIST_AFTER_ROTATION'])

    def test_cors_production_configuration(self):
        import os
        from unittest.mock import patch
        with patch.dict(os.environ, {'CORS_ALLOWED_ORIGINS': 'https://frontend.example.com', 'DEBUG': 'False', 'TESTING': 'False'}):
            cors_raw = os.environ.get('CORS_ALLOWED_ORIGINS', '')
            origins = [o.strip() for o in cors_raw.split(',') if o.strip()]
            allow_all = False if cors_raw else False
            self.assertEqual(origins, ['https://frontend.example.com'])
            self.assertFalse(allow_all)

    def test_allowed_hosts_configuration(self):
        import os
        from unittest.mock import patch
        with patch.dict(os.environ, {'ALLOWED_HOSTS': 'api.syncflow.ai,syncflow.ai'}):
            hosts_raw = os.environ.get('ALLOWED_HOSTS')
            hosts = [h.strip() for h in hosts_raw.split(',') if h.strip()]
            self.assertEqual(hosts, ['api.syncflow.ai', 'syncflow.ai'])
            self.assertNotIn('*', hosts)

