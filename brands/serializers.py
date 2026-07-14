from rest_framework import serializers
from .models import Brand, BrandVoice, BrandGuideline, BrandAsset


class BrandVoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandVoice
        fields = ("tone", "description", "do_list", "dont_list")


class BrandSerializer(serializers.ModelSerializer):
    voice = BrandVoiceSerializer(required=False)

    class Meta:
        model = Brand
        fields = ("id", "workspace", "name", "website", "industry", "target_audience", "mission", "vision", "keywords", "primary_color", "secondary_color", "logo", "voice", "created_at", "updated_at")
        read_only_fields = ("id", "workspace", "created_at", "updated_at")

    def create(self, validated_data):
        voice = validated_data.pop("voice", None)
        brand = Brand.objects.create(**validated_data)
        if voice:
            BrandVoice.objects.create(brand=brand, **voice)
        return brand

    def update(self, instance, validated_data):
        voice = validated_data.pop("voice", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        if voice is not None:
            BrandVoice.objects.update_or_create(brand=instance, defaults=voice)
        return instance
