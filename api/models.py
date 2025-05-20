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
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE)

class Form(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    project = models.ForeignKey(Project, related_name='forms', on_delete=models.CASCADE)
    table = models.OneToOneField(DynamicTable, on_delete=models.CASCADE, related_name='form')
    questions = models.JSONField(help_text="Store all questions in JSON format")

    def __str__(self):
        return self.name