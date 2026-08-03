from rest_framework import serializers
from .models import RevenueRecord, ExpenseRecord, Subscription

class RevenueRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RevenueRecord
        fields = '__all__'
        read_only_fields = ['user']

class ExpenseRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseRecord
        fields = '__all__'
        read_only_fields = ['user']

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = '__all__'
        read_only_fields = ['user']
