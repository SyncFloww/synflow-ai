from rest_framework import serializers
from .models import SupportTicket, CustomerHealth

class SupportTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = '__all__'
        read_only_fields = ['user']

class CustomerHealthSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerHealth
        fields = '__all__'
        read_only_fields = ['user']
