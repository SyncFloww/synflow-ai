from django.db import models
from django.contrib.auth.models import User

class SupportTicket(models.Model):
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    title = models.CharField(max_length=255)
    customer_name = models.CharField(max_length=255)
    priority = models.CharField(max_length=50, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='open')
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket #{self.id}: {self.title} ({self.status})"

class CustomerHealth(models.Model):
    RISK_CHOICES = (
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk Churn'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customer_healths')
    customer_name = models.CharField(max_length=255)
    health_score = models.IntegerField(default=100)  # 0 to 100
    risk_status = models.CharField(max_length=50, choices=RISK_CHOICES, default='low')
    last_interaction = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_name} - Health: {self.health_score}%"
