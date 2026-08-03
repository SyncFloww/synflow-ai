from django.db import models
from django.contrib.auth.models import User

class Lead(models.Model):
    STATUS_CHOICES = (
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('lost', 'Lost'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leads')
    name = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    email = models.EmailField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='new')
    deal_size = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.company})"

class Deal(models.Model):
    STAGE_CHOICES = (
        ('prospecting', 'Prospecting'),
        ('negotiation', 'Negotiation'),
        ('won', 'Closed Won'),
        ('lost', 'Closed Lost'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deals')
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='deals')
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    stage = models.CharField(max_length=50, choices=STAGE_CHOICES, default='prospecting')
    probability = models.IntegerField(default=20)  # percentage
    expected_close_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - ${self.amount}"

class Company(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='companies')
    name = models.CharField(max_length=255)
    domain = models.CharField(max_length=255, blank=True, default='')
    industry = models.CharField(max_length=100, blank=True, default='')
    employee_count = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Contact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacts')
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='contacts')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True, default='')
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()

class Pipeline(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pipelines')
    name = models.CharField(max_length=255)
    stages = models.JSONField(default=list) # e.g. ["Prospecting", "Qualification", "Proposal", "Closed Won"]
    is_default = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Activity(models.Model):
    ACTIVITY_TYPES = (
        ('call', 'Call'),
        ('email', 'Email'),
        ('meeting', 'Meeting'),
        ('note', 'Note'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='crm_activities')
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES, default='note')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.activity_type.capitalize()}: {self.title}"

class CustomerJourney(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customer_journeys')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='journeys')
    stage = models.CharField(max_length=100) # e.g. "Awareness", "Consideration", "Decision", "Retention"
    touchpoint = models.CharField(max_length=255)
    channel = models.CharField(max_length=100)
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.contact.email} - {self.stage} ({self.touchpoint})"

class CampaignAttribution(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attributions')
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='attributions')
    campaign_name = models.CharField(max_length=255)
    attribution_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    revenue_share = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.campaign_name} -> {self.deal.title} ({self.attribution_percentage}%)"

