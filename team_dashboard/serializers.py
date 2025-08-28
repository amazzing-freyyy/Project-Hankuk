from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import *

class WUDSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wake_Up_Data
        fields = '__all__'
        read_only_fields = ['slug', 'user']

class PTDSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S", input_formats=["%Y-%m-%dT%H:%M:%S"])
    
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
    groups = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name'
    )

    class Meta:
        model = User
        fields = "__all__"

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

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['groups'] = [group.name for group in user.groups.all()]
        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # Add extra response data
        data['username'] = self.user.username
        data['groups'] = [group.name for group in self.user.groups.all()]
        return data