from django.db import models
from django.contrib.auth.models import User

class Project(models.Model):
    name = models.CharField(max_length=100, unique=True)

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('coach', 'Coach'),
        ('athlete', 'Athlete'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

class DynamicTable(models.Model):
    title = models.CharField(max_length=100)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    schema = models.JSONField()

class DynamicData(models.Model):
    table = models.ForeignKey(DynamicTable, on_delete=models.CASCADE)
    row = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)