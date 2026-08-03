from django.db import models
from django.contrib.auth.models import User

class Employee(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('on_leave', 'On Leave'),
        ('terminated', 'Terminated'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='employees')
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=150)
    department = models.CharField(max_length=150)
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=5000.00)
    performance_rating = models.DecimalField(max_digits=3, decimal_places=2, default=4.00)  # out of 5.0
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active')
    hired_at = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.role} ({self.department})"

class LeaveRequest(models.Model):
    TYPE_CHOICES = (
        ('sick', 'Sick Leave'),
        ('vacation', 'Annual Vacation'),
        ('unpaid', 'Unpaid Leave'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_requests')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leaves')
    leave_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='vacation')
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Leave request for {self.employee.name} ({self.status})"
