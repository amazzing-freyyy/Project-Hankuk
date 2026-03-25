from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import *
from django.contrib.auth.models import User, Group
import logging

logger = logging.getLogger('project_hankuk')

class MainDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Main_data
        fields = '__all__'
        read_only_fields = ['slug', 'user']
        lookupfield = 'slug'
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

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
    groups = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Group.objects.all()
    )

    class Meta:
        model = User
        fields = [ 'username', 'password', 'first_name', 'last_name', 'email', 'is_active', 'groups', 'profile']

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})

        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update profile
        profile = instance.profile
        if 'gender' in profile_data:
            profile.gender = profile_data['gender']
        profile.save()

        return instance
    
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)
    
    def create(self, validated_data):
        profile_data = validated_data.pop("profile", None)  # take out profile info if present
        group_data = validated_data.pop("groups", [])  # take out group info if present
        password = validated_data.pop('password')

        user = User.objects.create_user(**validated_data)

        if group_data:
            for group_name in group_data:
                group, created = Group.objects.get_or_create(name=group_name)
                user.groups.add(group)

        user.set_password(password)
        user.save()

        # If client included profile data, create it
        if profile_data:
            Profile.objects.create(user=user, **profile_data)
        else:
            Profile.objects.create(user=user)



        return user

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['name']

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