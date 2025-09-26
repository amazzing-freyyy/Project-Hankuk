from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import *
from django.contrib.auth.models import User, Group

class MainDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wake_Up_Data
        fields = '__all__'
        read_only_fields = ['slug', 'user', 'date', 'data_collection']
        lookupfield = 'slug'

class WUDSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wake_Up_Data
        fields = '__all__'
        read_only_fields = ['slug', 'user']
        lookupfield = 'slug'

class PTDSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S", input_formats=["%Y-%m-%dT%H:%M:%S"])
    
    class Meta:
        model = Post_Training_Data
        fields = '__all__'
        read_only_fields = ['slug', 'user']
        lookupfield = 'slug'
    
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['gender']

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    profile = ProfileSerializer(required=False)
    groups = serializers.ListField(
        child=serializers.CharField(),  # group names
        required=False,
        write_only=True  # we usually don’t expose groups on read here
    )

    class Meta:
        model = User
        fields = [ 'username', 'password', 'first_name', 'last_name', 'email', 'is_active', 'groups', 'profile']

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
    
    def create(self, validated_data):
        profile_data = validated_data.pop("profile", None)  # take out profile info if present
        group_data = validated_data.pop("groups", [])  # take out group info if present

        user = User.objects.create_user(**validated_data)

        # If client included profile data, create it
        if profile_data:
            Profile.objects.create(user=user, **profile_data)
        else:
            Profile.objects.create(user=user)
        
        if group_data:
            for group_name in group_data:
                group, created = Group.objects.get_or_create(name=group_name)
                user.groups.add(group)
            user.save()

        return user

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