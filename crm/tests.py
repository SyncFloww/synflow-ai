from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from .models import Lead, Deal, Company, Contact, Pipeline, Activity, CustomerJourney, CampaignAttribution

class CRMModuleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='crmuser', email='crm@example.com', password='Password123!')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_lead_and_deal_lifecycle(self):
        lead = Lead.objects.create(user=self.user, name='John Doe', company='Acme Corp', email='john@acme.com', deal_size=50000.00)
        response = self.client.get('/api/crm/leads/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        deal = Deal.objects.create(user=self.user, lead=lead, title='Acme Enterprise Deal', amount=50000.00)
        response = self.client.get('/api/crm/deals/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_company_and_contact_endpoints(self):
        company = Company.objects.create(user=self.user, name='TechCorp', domain='techcorp.io', industry='SaaS')
        contact = Contact.objects.create(user=self.user, company=company, first_name='Jane', email='jane@techcorp.io')

        response = self.client.get('/api/crm/companies/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get('/api/crm/contacts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_pipeline_and_activity_endpoints(self):
        pipeline = Pipeline.objects.create(user=self.user, name='Standard Sales Pipeline', stages=['Discovery', 'Demo', 'Closed Won'])
        activity = Activity.objects.create(user=self.user, title='Initial Intro Call', activity_type='call')

        response = self.client.get('/api/crm/pipelines/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.get('/api/crm/activities/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
