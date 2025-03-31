from django.http.response import HttpResponse as HttpResponse
from django.contrib.auth.models import User, Group
import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import *
from .serializers import *


logger = logging.getLogger(__name__) 

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_view(request):
    return Response({'message': f'Hello, {request.user.username}! This is a protected route.'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_wakeUpData(request):
    user = request.user
    if user.groups.filter(name='athletes').exists():
        data = Wake_Up_Data.objects.filter(user=user).all()
        username = user.username
    else:
        username= request.data.get('athleteUserName')
        user = User.objects.filter(username=username).first()
        data = Wake_Up_Data.objects.filter(user=user).all()
    
    serializer= WUDSerializer(data, many=True)
    return Response({'athleteUserName':username, 'graph_data':serializer.data})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_postTrainingData(request):
    user = request.user
    if user.groups.filter(name='athletes').exists():
        data = Post_Training_Data.objects.filter(user=user).all()
        username = user.username
    else:
        username= request.data.get('athleteUserName')
        user = User.objects.filter(username=username).first()
        data = Post_Training_Data.objects.filter(user=user).all()
    
    serializer= PTDSerializer(data, many=True)
    return Response({'athleteUserName':username, 'graph_data':serializer.data})

@api_view(['POST'])
def register_user(request):
    username = request.data.get('username')
    password = request.data.get('password')
    group = request.data.get('group')
    gender = request.data.get('gender')

    if not username or not password:
        return Response({"error": "Usuario y contraseña son necesarios."}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({"error": "Usuario ya existe."}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, password=password)
    user_group, _ = Group.objects.get_or_create(name=group)
    user.groups.add(user_group)
    user.profile.gender = gender
    user.profile.save()
    return Response({"message": "User registered successfully!"}, status=status.HTTP_201_CREATED)