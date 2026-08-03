from rest_framework import serializers
from .models import Lead, Deal, Company, Contact, Pipeline, Activity, CustomerJourney, CampaignAttribution

class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = '__all__'
        read_only_fields = ['user']

class DealSerializer(serializers.ModelSerializer):
    lead_name = serializers.ReadOnlyField(source='lead.name')
    lead_company = serializers.ReadOnlyField(source='lead.company')

    class Meta:
        model = Deal
        fields = '__all__'
        read_only_fields = ['user']

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'
        read_only_fields = ['user']

class ContactSerializer(serializers.ModelSerializer):
    company_name = serializers.ReadOnlyField(source='company.name')

    class Meta:
        model = Contact
        fields = '__all__'
        read_only_fields = ['user']

class PipelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pipeline
        fields = '__all__'
        read_only_fields = ['user']

class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = '__all__'
        read_only_fields = ['user']

class CustomerJourneySerializer(serializers.ModelSerializer):
    contact_email = serializers.ReadOnlyField(source='contact.email')

    class Meta:
        model = CustomerJourney
        fields = '__all__'
        read_only_fields = ['user']

class CampaignAttributionSerializer(serializers.ModelSerializer):
    deal_title = serializers.ReadOnlyField(source='deal.title')

    class Meta:
        model = CampaignAttribution
        fields = '__all__'
        read_only_fields = ['user']

