from rest_framework import serializers
from .models import *

class WUDSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wake_Up_Data
        fields = '__all__'
        read_only_fields = ['slug', 'user']

class PTDSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post_Training_Data
        fields = '__all__'
        read_only_fields = ['slug', 'user']
    
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = "__all__"

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    profile = ProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password', 'profile']

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        profile_data = validated_data.pop('profile', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()

        # Update profile if present
        if profile_data:
            profile = instance.profile  # assumes profile is already created
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        return instance