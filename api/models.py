# models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    is_coach = models.BooleanField(default=False)
    is_athlete = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

class Project(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    users = models.ManyToManyField(User, related_name="projects")

class FormSchema(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    schema = models.JSONField()  # defines field types, labels, etc., using safe keys

class FormSubmission(models.Model):
    form = models.ForeignKey(FormSchema, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField()  # actual values using safe keys

class TableConfig(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    form = models.ForeignKey(FormSchema, on_delete=models.CASCADE)
    columns = models.JSONField()  # list of safe field keys to show
    filters = models.JSONField(blank=True, null=True)

class GraphConfig(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    form = models.ForeignKey(FormSchema, on_delete=models.CASCADE)
    graph_type = models.CharField(max_length=20, choices=[
        ('line', 'Line'),
        ('bar', 'Bar'),
        ('scatter', 'Scatter'),
    ])
    x_field = models.CharField(max_length=100)  # safe key
    y_field = models.CharField(max_length=100)  # safe key
    computed_fields = models.JSONField(blank=True, null=True)  # {"new_field": "expression using safe keys"}
    filters = models.JSONField(blank=True, null=True)

