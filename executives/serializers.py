from rest_framework import serializers
from .models import ExecutiveMeeting

class ExecutiveMeetingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecutiveMeeting
        fields = '__all__'
        read_only_fields = ['user']
