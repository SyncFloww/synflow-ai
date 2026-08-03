from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LeadViewSet, DealViewSet, CompanyViewSet, ContactViewSet,
    PipelineViewSet, ActivityViewSet, CustomerJourneyViewSet, CampaignAttributionViewSet
)

router = DefaultRouter()
router.register('leads', LeadViewSet, basename='lead')
router.register('deals', DealViewSet, basename='deal')
router.register('companies', CompanyViewSet, basename='company')
router.register('contacts', ContactViewSet, basename='contact')
router.register('pipelines', PipelineViewSet, basename='pipeline')
router.register('activities', ActivityViewSet, basename='activity')
router.register('customer-journeys', CustomerJourneyViewSet, basename='customer-journey')
router.register('campaign-attributions', CampaignAttributionViewSet, basename='campaign-attribution')

urlpatterns = [
    path('', include(router.urls)),
]

