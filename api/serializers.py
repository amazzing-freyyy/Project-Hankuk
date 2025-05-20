from rest_framework import serializers
from django.contrib.auth.models import User
from api.models import UserProfile, Project, DynamicTable, Form

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
    
class FormSerializer(serializers.ModelSerializer):
    class Meta:
        model = Form
        fields = '__all__'

    def validate_questions(self, value):
        for key, question in value.items():
            if not isinstance(question, dict):
                raise serializers.ValidationError(f"Each question must be a dictionary: issue with '{key}'")

            required_fields = ['text', 'type', 'input']
            for field in required_fields:
                if field not in question:
                    raise serializers.ValidationError(f"Missing '{field}' in question '{key}'")

            if question['input'] in ['drop down', 'select', 'radio buttons', 'slider'] and 'values' not in question:
                raise serializers.ValidationError(f"Input type '{question['input']}' requires a 'values' field in question '{key}'")

        return value
    
    def validate_table(self, value):
        user_project = self.context['request'].user.userprofile.project
        if value.project != user_project:
            raise serializers.ValidationError("Table does not belong to your project.")
        return value