from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from workspaces.models import Workspace, WorkspaceMember
from social.models import Brand, BrandProfile


class BrandInterviewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='brand-owner')
        self.workspace = Workspace.objects.create(name='Brand workspace', owner=self.user)
        self.member = WorkspaceMember.objects.create(workspace=self.workspace, user=self.user, role='OWNER')
        self.brand = Brand.objects.create(workspace=self.workspace, name='Bakery')
        self.url = f'/api/social/brands/{self.brand.id}/onboarding/'
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.answers = {'description': 'A local bakery', 'products_services': 'Bread\nCakes',
                        'target_audience': 'Families nearby', 'tone': 'Warm', 'goal': 'More local orders'}

    def test_partial_answers_resume(self):
        response = self.client.patch(self.url, {'answers': {'description': 'Fresh bread'}}, format='json')
        self.assertEqual(response.status_code, 200)
        resumed = self.client.get(self.url).data
        self.assertEqual(resumed['answers']['description'], 'Fresh bread')
        self.assertIn('goal', resumed['missing'])
        self.assertFalse(resumed['completed'])

    def test_completion_syncs_profile_and_goal(self):
        response = self.client.patch(self.url, {'answers': self.answers, 'complete': True}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['completed'])
        self.brand.refresh_from_db()
        self.assertEqual(self.brand.profile.products_services, ['Bread', 'Cakes'])
        self.assertEqual(self.brand.brand_voice.goal, 'More local orders')
        self.assertEqual(self.brand.description, 'A local bakery')

    def test_incomplete_completion_has_no_partial_writes(self):
        response = self.client.patch(self.url, {'answers': {'description': 'Unsaved'}, 'complete': True}, format='json')
        self.assertEqual(response.status_code, 400)
        self.brand.refresh_from_db()
        self.assertEqual(self.brand.description, '')
        self.assertFalse(BrandProfile.objects.filter(brand=self.brand).exists())

    def test_non_members_cannot_read_or_write(self):
        other = User.objects.create_user(username='outsider')
        self.client.force_authenticate(other)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.patch(self.url, {'answers': self.answers}, format='json').status_code, 404)

    def test_members_can_read_but_not_write(self):
        self.member.role = 'MEMBER'
        self.member.save()
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(self.client.patch(self.url, {'answers': self.answers}, format='json').status_code, 403)

    def test_invalid_payloads_are_rejected(self):
        for answers in ({'unknown': 'value'}, {'description': 'x' * 2001}, {'tone': 'x' * 256}, ['bad']):
            with self.subTest(answers=answers):
                self.assertEqual(self.client.patch(self.url, {'answers': answers}, format='json').status_code, 400)

    def test_editing_completed_profile_requires_review_again(self):
        self.client.patch(self.url, {'answers': self.answers, 'complete': True}, format='json')
        response = self.client.patch(self.url, {'answers': {'goal': 'More leads'}}, format='json')
        self.assertFalse(response.data['completed'])

    def test_profile_endpoint_cannot_bypass_completion_validation(self):
        self.client.get(self.url)
        response = self.client.patch(f'/api/social/brands/{self.brand.id}/profile/',
                                     {'onboarding_completed': True}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(BrandProfile.objects.get(brand=self.brand).onboarding_completed)

    def test_unauthenticated_access_is_rejected(self):
        self.client.force_authenticate(user=None)
        self.assertIn(self.client.get(self.url).status_code, (401, 403))
