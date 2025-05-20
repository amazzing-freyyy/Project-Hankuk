from rest_framework import serializers
from django.contrib.auth.models import User
from api.models import UserProfile, Project

class TableCreateSerializer(serializers.Serializer):
    Title = serializers.CharField()
    project = serializers.CharField()
    data = serializers.DictField()

class DataSubmitSerializer(serializers.Serializer):
    Title = serializers.CharField()
    data = serializers.DictField()

class TableStructureSerializer(serializers.Serializer):
    Title = serializers.CharField()
    project = serializers.CharField()
    data = serializers.DictField()

class ProcessDataSerializer(serializers.Serializer):
    Title = serializers.CharField()
    data = serializers.DictField(child=serializers.DictField())

class DataUpdateSerializer(serializers.Serializer):
    Title = serializers.CharField()
    data = serializers.DictField()

class UserSignupSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    project = serializers.CharField()
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES)

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        project, _ = Project.objects.get_or_create(name=validated_data['project'])
        UserProfile.objects.create(user=user, project=project, role=validated_data['role'])
        return user
