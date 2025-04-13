from django.http.response import HttpResponse as HttpResponse
from django.contrib.auth.models import User, Group
import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
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

@api_view(['GET'])
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

    graph_data= {dates[i].strftime('%d, %b, %Y'): {'hr':hr[i], 'hr_z_score':p_z_score[i],'lnrmssd': lnrmssd[i], 'linfrmssd':p_linfrmssd[i], 'lsuprmssd':p_lsuprmssd[i]} for i in range(len(dates))}

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

    graph_data= graph_data= {dates[i].strftime('%d, %b, %Y'): {'ss': ss[i], 'sp':sp[i], 'ss_z_score':p_z_score[i]} for i in range(len(dates))}

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
    
    graph_data={'date':data['date'].strftime('%d, %b, %Y'), 'h_sleep':data['hours_of_sleep'], 'wellness':data['emotional_wellness'], 'q_sleep':data['quality_of_sleep'], 'recovery':data['tiredness'], 'comments':data['comments'], 'menstruation':data['menstruation'], 'pain':data['muscle_pain'], 'chispa':data['chispa']}
    return Response({'athleteUserName':username, 'graph_data':graph_data})

@api_view(['GET'])
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_rpe2XtimeData(request):
    user = request.user
    if user.groups.filter(name='athletes').exists():
        data = Post_Training_Data.objects.filter(user=user).values('date', 'perceived_strain_of_activity', 'time_of_activity', 'type_of_activity').all()
        username = user.username
    else:
        username= request.data.get('athleteUserName')
        user = User.objects.filter(username=username).first()
        data = Post_Training_Data.objects.filter(user=user).values('date', 'perceived_strain_of_activity', 'time_of_activity', 'type_of_activity').all()
    
    dates= list(data.values_list('date', flat=True))

    rpe= np.array(list(data.values_list('perceived_strain_of_activity'))).flatten()
    time= np.array(list(data.values_list('time_of_activity'))).flatten()

    rpe2Xtime=  rpe * rpe * time

    activity= np.array(list(data.values_list('type_of_activity'))).flatten()

    graph_data = {dates[i].strftime('%d, %b, %Y'): {'rpe2Xtime': rpe2Xtime[i], 'activity':activity[i]} for i in range(len(dates))}

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

    graph_data= {dates[i].strftime('%d, %b, %Y %H:%M'): {'pain':pain[i], 'comments':comments[i]} for i in range(len(dates))}
    
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