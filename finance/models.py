from django.db import models
from django.contrib.auth.models import User

class RevenueRecord(models.Model):
    SOURCE_CHOICES = (
        ('subscription', 'Subscription MRR'),
        ('consulting', 'Professional Services'),
        ('one_off', 'One-off Platform License'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='revenues')
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, default='subscription')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    date = models.DateField()
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_source_display()}: ${self.amount}"

class ExpenseRecord(models.Model):
    CATEGORY_CHOICES = (
        ('marketing', 'Marketing & Ads'),
        ('hosting', 'Server Hosting & AI APIs'),
        ('salaries', 'Payroll & Salaries'),
        ('office', 'Rent & General Admin'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='hosting')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    date = models.DateField()
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_category_display()}: ${self.amount}"

class Subscription(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('trialing', 'Trialing'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    company_name = models.CharField(max_length=255)
    plan_name = models.CharField(max_length=100, default='Pro Plan')
    mrr = models.DecimalField(max_digits=12, decimal_places=2, default=199.00)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active')
    start_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company_name} - ${self.mrr}/mo"
