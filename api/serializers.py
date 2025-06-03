# serializers.py
from rest_framework import serializers
from .models import *

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_coach', 'is_athlete', 'is_admin')

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'

class FormSchemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormSchema
        fields = '__all__'

class FormSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormSubmission
        fields = '__all__'

class TableConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = TableConfig
        fields = '__all__'

class GraphConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = GraphConfig
        fields = '__all__'