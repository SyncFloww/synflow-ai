from rest_framework import serializers
from .models import MarketplaceApp, MarketplaceItem, PromptPack, PluginExtension

class MarketplaceAppSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketplaceApp
        fields = '__all__'

MarketplaceItemSerializer = MarketplaceAppSerializer

class PromptPackSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptPack
        fields = '__all__'

class PluginExtensionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PluginExtension
        fields = '__all__'

