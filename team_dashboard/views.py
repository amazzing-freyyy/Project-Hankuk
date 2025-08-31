from django.http.response import HttpResponse as HttpResponse
from django.contrib.auth.models import User, Group
import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.viewsets import ModelViewSet
from .models import *
from .serializers import *
from .permissions import *
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
import datetime
from django_filters.rest_framework import DjangoFilterBackend

logger = logging.getLogger(__name__) 

class WUDViewSet(ModelViewSet):
    queryset = Wake_Up_Data.objects.all()
    serializer_class = WUDSerializer
    permission_classes = [IsAuthenticated, IsCoachOrOwner]
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['date', 'user__username']
    ordering_fields = ['date']
    ordering = ['-date']

    def perform_create(self, serializer):
        user = User.objects.get(username=self.request.data["username"])

        return serializer.save(user=user)

class PTDViewSet(ModelViewSet):
    queryset = Post_Training_Data.objects.all()
    serializer_class = PTDSerializer
    permission_classes = [IsAuthenticated, IsCoachOrOwner]
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['date', 'user__username']

    def perform_create(self, serializer):
        user = User.objects.get(username=self.request.data["username"])

        return serializer.save(user=user)

class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'username'
    filter_backends = [DjangoFilterBackend]

    filterset_fields = ['username', 'first_name', 'last_name', 'email', 'groups__name', 'is_active']
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsCoachOrOwner(), IsAuthenticated()]
        return [AllowAny()]
    
class ProfileViewSet(ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated, IsCoachOrOwner]
    lookup_field = 'user__username'

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class= MyTokenObtainPairSerializer

@api_view(['POST'])
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

    if not data.exists():
        return Response({'error': 'No data'}, status=status.HTTP_404_NOT_FOUND)

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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_ssData(request):
    user = request.user
    if user.groups.filter(name='athletes').exists():
        username = user.username
    else:
        username= request.data.get('athleteUserName')
        user = User.objects.filter(username=username).first()

    data = Wake_Up_Data.objects.filter(user=user).values('date', 'SDNN', 'RMSSD').all()

    if not data.exists():
        return Response({'error': 'No data'}, status=status.HTTP_404_NOT_FOUND)

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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_wellnessData(request):
    user = request.user
    is_athlete = user.groups.filter(name='athletes').exists()

    if is_athlete:
        username=user.username
    else:
        username= request.data.get('athleteUserName')
        user = User.objects.filter(username=username).first()

    date_str = request.data.get('date')
    if date_str:
        date = datetime.date.fromisoformat(date_str)
        data = Wake_Up_Data.objects.filter(user=user, date=date).values('date', 'hours_of_sleep', 'emotional_wellness', 'quality_of_sleep', 'tiredness', 'comments', 'menstruation', 'muscle_pain', 'chispa').order_by('-date').first()
    else:
        data = Wake_Up_Data.objects.filter(user=user).values('date', 'hours_of_sleep', 'emotional_wellness', 'quality_of_sleep', 'tiredness', 'comments', 'menstruation', 'muscle_pain', 'chispa').order_by('-date').first()

    if not data:
        return Response({'error': 'No data'}, status=status.HTTP_404_NOT_FOUND)
    
    graph_data={'date':data['date'].strftime('%Y-%m-%d'), 'h_sleep':data['hours_of_sleep'], 'wellness':data['emotional_wellness'], 'q_sleep':data['quality_of_sleep'], 'recovery':data['tiredness'], 'comments':data['comments'], 'menstruation':data['menstruation'], 'pain':data['muscle_pain'], 'chispa':data['chispa']}
    return Response({'athleteUserName':username, 'graph_data':graph_data})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_rpe2XtimeData(request):
    user = request.user
    if user.groups.filter(name='athletes').exists():
        username = user.username
    else:
        username= request.data.get('athleteUserName')
        user = User.objects.filter(username=username).first()

    time_threshold= datetime.time(12,0)
    data = [Post_Training_Data.objects.filter(user=user, date__time__lt=time_threshold).values('date', 'perceived_strain_of_activity', 'time_of_activity', 'type_of_activity').all(),
                Post_Training_Data.objects.filter(user=user, date__time__gte=time_threshold).values('date', 'perceived_strain_of_activity', 'time_of_activity', 'type_of_activity').all(),]

    if not data[0].exists() and not data[1].exists():
        return Response({'error': 'No data'}, status=status.HTTP_404_NOT_FOUND)
    
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

@api_view(['POST'])
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
    
    if not data.exists():
        return Response({'error': 'No data'}, status=status.HTTP_404_NOT_FOUND)

    dates= list(data.values_list('date', flat=True))

    time= np.array(list(data.values_list('time_of_activity'))).flatten()

    activity= np.array(list(data.values_list('type_of_activity'))).flatten()

    graph_data = {dates[i].strftime('%Y-%m-%d %H:%M'): {'activity':activity[i], 'duration':time[i]} for i in range(len(dates))}

    return Response({'athleteUserName':username, 'graph_data':graph_data})

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