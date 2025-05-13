from django.http.response import HttpResponse as HttpResponse
from django.contrib.auth.models import User, Group
import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import *
from .serializers import *
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
import datetime

logger = logging.getLogger(__name__) 

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_view(request):
    return Response({'message': f'Hello, {request.user.username}! This is a protected route.'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def new_WUD(request):
    user= request.user
    data= request.data.copy() 

    serializer = WUDSerializer(data=data)
    if serializer.is_valid():
        serializer.save(user = user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def new_PT(request):
    user= request.user
    data= request.data.copy() 

    serializer = PTDSerializer(data=data)
    if serializer.is_valid():
        serializer.save(user = user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_allWakeUpData(request):
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_lnrmssdData(request):
    user = request.user
    if user.groups.filter(name='athletes').exists():
        data = Wake_Up_Data.objects.filter(user=user).values('date', 'RMSSD', 'HR').all()
        username = user.username
    else:
        username= request.data.get('athleteUserName')
        user = User.objects.filter(username=username).first()
        data = Wake_Up_Data.objects.filter(user=user).values('date', 'RMSSD', 'HR').all()
    
    dates= list(data.values_list('date', flat=True))

    hr= np.array(list(data.values_list('HR',flat=True)))

    rmssd= np.array(list(data.values_list('RMSSD'))).flatten()
    
    lnrmssd= np.log(rmssd)

    interval = 7
    windows= sliding_window_view(lnrmssd, window_shape=interval)

    linfrmssd= np.abs(0.06 + windows.std(axis=1) - windows.mean(axis=1))
    lsuprmssd= np.abs(0.06 + windows.std(axis=1) + windows.mean(axis=1))

    p_len= interval - 1 
    p_linfrmssd= np.concatenate([np.full(p_len, 'NaN'), linfrmssd])
    p_lsuprmssd= np.concatenate([np.full(p_len, 'NaN'), lsuprmssd])

    windows_hr= sliding_window_view(hr, window_shape=interval)
    means= windows_hr.mean(axis= 1)
    stds= windows_hr.std(axis= 1)
    target_val= hr[interval-1:]
    z_score= (target_val - means) / stds

    p_z_score= np.concatenate([np.full(p_len, 'NaN'), z_score])

    graph_data= {dates[i].strftime('%Y-%m-%d'): {'hr':hr[i], 'hr_z_score':p_z_score[i],'lnrmssd': lnrmssd[i], 'linfrmssd':p_linfrmssd[i], 'lsuprmssd':p_lsuprmssd[i]} for i in range(len(dates))}

    return Response({'athleteUserName':username, 'graph_data':graph_data})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ssData(request):
    user = request.user
    if user.groups.filter(name='athletes').exists():
        data = Wake_Up_Data.objects.filter(user=user).values('date', 'SDNN', 'RMSSD').all()
        username = user.username
    else:
        username= request.data.get('athleteUserName')
        user = User.objects.filter(username=username).first()
        data = Wake_Up_Data.objects.filter(user=user).values('date', 'SDNN', 'RMSSD').all()

    dates= list(data.values_list('date', flat=True))

    rmssd= np.array(list(data.values_list('RMSSD'))).flatten()
    sdnn= np.array(list(data.values_list('SDNN'))).flatten()

    ss= 1000 / (sdnn / 0.7995) + 5.1174
    sp= ss / (0.7071 * rmssd)

    interval = 7
    windows= sliding_window_view(ss, window_shape=interval)
    means= windows.mean(axis= 1)
    stds= windows.std(axis= 1)
    target_val= ss[interval-1:]
    z_score= (target_val - means) / stds

    p_len= interval-1
    p_z_score= np.concatenate([np.full(p_len, 'NaN'), z_score])

    graph_data= graph_data= {dates[i].strftime('%Y-%m-%d'): {'ss': ss[i], 'sp':sp[i], 'ss_z_score':p_z_score[i]} for i in range(len(dates))}

    return Response({'athleteUserName':username, 'graph_data':graph_data})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wellnessData(request):
    user = request.user
    is_athlete = user.groups.filter(name='athletes').exists()

    if is_athlete:
        username=user.username
    else:
        if not username:
            return Response({'error': 'Missing "athleteUserName" field'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(username=username).first()

    date_str = request.data.get('date')
    if date_str:
        date = datetime.date.fromisoformat(date_str)
        data = Wake_Up_Data.objects.filter(user=user, date=date).values('date', 'hours_of_sleep', 'emotional_wellness', 'quality_of_sleep', 'tiredness', 'comments', 'menstruation', 'muscle_pain', 'chispa').order_by('-date').first()
    else:
        data = Wake_Up_Data.objects.filter(user=user).values('date', 'hours_of_sleep', 'emotional_wellness', 'quality_of_sleep', 'tiredness', 'comments', 'menstruation', 'muscle_pain', 'chispa').order_by('-date').first()
    
    graph_data={'date':data['date'].strftime('%Y-%m-%d'), 'h_sleep':data['hours_of_sleep'], 'wellness':data['emotional_wellness'], 'q_sleep':data['quality_of_sleep'], 'recovery':data['tiredness'], 'comments':data['comments'], 'menstruation':data['menstruation'], 'pain':data['muscle_pain'], 'chispa':data['chispa']}
    return Response({'athleteUserName':username, 'graph_data':graph_data})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_allPostTrainingData(request):
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_rpe2XtimeData(request):
    user = request.user
    if user.groups.filter(name='athletes').exists():
        time_threshold= datetime.time(12,0)
        data = [Post_Training_Data.objects.filter(user=user, date__time__lt=time_threshold).values('date', 'perceived_strain_of_activity', 'time_of_activity', 'type_of_activity').all(),
                Post_Training_Data.objects.filter(user=user, date__time__gte=time_threshold).values('date', 'perceived_strain_of_activity', 'time_of_activity', 'type_of_activity').all(),]
        username = user.username
    else:
        username= request.data.get('athleteUserName')
        user = User.objects.filter(username=username).first()
        data = Post_Training_Data.objects.filter(user=user).values('date', 'perceived_strain_of_activity', 'time_of_activity', 'type_of_activity').all()
    
    dates= [list(data[0].values_list('date', flat=True)), 
            list(data[1].values_list('date', flat=True))]

    rpe= [np.array(list(data[0].values_list('perceived_strain_of_activity'))).flatten(),
          np.array(list(data[1].values_list('perceived_strain_of_activity'))).flatten()]

    time= [np.array(list(data[0].values_list('time_of_activity'))).flatten(),
           np.array(list(data[1].values_list('time_of_activity'))).flatten()]

    rpe2Xtime=  [rpe[0] * rpe[0] * time[0],
                 rpe[1] * rpe[1] * time[1]]

    activity= [np.array(list(data[0].values_list('type_of_activity'))).flatten(),
               np.array(list(data[1].values_list('type_of_activity'))).flatten()]

    graph_data = {'morning': {dates[0][i].strftime('%Y-%m-%d %H:%M'): {'rpe2Xtime': rpe2Xtime[0][i], 'activity':activity[0][i]} for i in range(len(dates[0]))},
                  'afternoon': {dates[1][i].strftime('%Y-%m-%d %H:%M'): {'rpe2Xtime': rpe2Xtime[1][i], 'activity':activity[1][i]} for i in range(len(dates[1]))}}

    return Response({'athleteUserName':username, 'graph_data':graph_data})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_lastWeeksTrainings(request):
    user = request.user

    date_str = request.data.get('date')
    if date_str:
        date= datetime.date.fromisoformat(date_str)
    else:
        date= datetime.date.today()

    if user.groups.filter(name='athletes').exists():
        username = user.username
    else:
        username= request.data.get('athleteUserName')
        user = User.objects.filter(username=username).first()

    data = Post_Training_Data.objects.filter(user=user, date__gte= date-datetime.timedelta(days=7), date__lte= date).values('date', 'type_of_activity', 'time_of_activity').all()
    
    dates= list(data.values_list('date', flat=True))

    time= np.array(list(data.values_list('time_of_activity'))).flatten()

    activity= np.array(list(data.values_list('type_of_activity'))).flatten()

    graph_data = {dates[i].strftime('%Y-%m-%d %H:%M'): {'activity':activity[i], 'duration':time[i]} for i in range(len(dates))}

    return Response({'athleteUserName':username, 'graph_data':graph_data})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_PTData(request):
    user = request.user
    is_athlete = user.groups.filter(name='athletes').exists()

    if is_athlete:
        username=user.username
    else:
        if not username:
            return Response({'error': 'Missing "athleteUserName" field'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(username=username).first()

    date_str = request.data.get('date')
    if date_str:
        date = datetime.datetime.fromisoformat(date_str)
        data = Post_Training_Data.objects.filter(user=user, date__gte=date, date__lt=date+datetime.timedelta(days=1)).values('date', 'pain', 'comments').order_by('date').all()
    else:
        data = Post_Training_Data.objects.filter(user=user, date__gte=datetime.date.today()).values('date', 'pain', 'comments').order_by('date').all()

    if not data:
        return Response({'error': 'No training data found'}, status=status.HTTP_404_NOT_FOUND)
    
    dates = list(data.values_list('date', flat=True))

    pain = list(data.values_list('pain', flat=True))

    comments =list(data.values_list('comments', flat=True))

    graph_data= {dates[i].strftime('%Y-%m-%d %H:%M'): {'pain':pain[i], 'comments':comments[i]} for i in range(len(dates))}
    
    return Response({'athleteUserName':username, 'graph_data':graph_data})

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

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_user(request, username):
    try:
        instance = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    partial = request.method == 'PATCH'
    serializer = UserSerializer(instance, data=request.data, partial=partial)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_WUD(request, slug):
    try:
        instance = Wake_Up_Data.objects.get(slug=slug)
    except Wake_Up_Data.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    partial = request.method == 'PATCH'
    serializer = WUDSerializer(instance, data=request.data, partial=partial)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_PT(request, slug):
    try:
        instance = Post_Training_Data.objects.get(slug=slug)
    except Post_Training_Data.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    partial = request.method == 'PATCH'
    serializer = PTDSerializer(instance, data=request.data, partial=partial)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    # Check if the requesting user is the author of the post
    if request.user != user and not request.user.is_staff:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    user.delete()
    return Response({'message': 'User deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_WUD(request, slug):
    try:
        data = Wake_Up_Data.objects.get(slug=slug)
    except Wake_Up_Data.DoesNotExist:
        return Response({'error': 'Data not found'}, status=status.HTTP_404_NOT_FOUND)

    # Check if the requesting user is the author of the post
    if request.user != data.user and not request.user.is_staff:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    data.delete()
    return Response({'message': 'Data deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_PT(request, slug):
    try:
        data = Post_Training_Data.objects.get(slug=slug)
    except Post_Training_Data.DoesNotExist:
        return Response({'error': 'Data not found'}, status=status.HTTP_404_NOT_FOUND)

    # Check if the requesting user is the author of the post
    if request.user != data.user and not request.user.is_staff:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    data.delete()
    return Response({'message': 'Data deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def users_in_group(request, group_name):
    try:
        group = Group.objects.get(name=group_name)
    except Group.DoesNotExist:
        return Response({'error': 'Group not found'}, status=status.HTTP_404_NOT_FOUND)

    users = group.user_set.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)