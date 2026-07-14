from django.contrib import admin
from .models import Brand, BrandVoice, BrandGuideline, BrandAsset
admin.site.register((Brand, BrandVoice, BrandGuideline, BrandAsset))
