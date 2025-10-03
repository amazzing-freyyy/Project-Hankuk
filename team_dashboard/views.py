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

class _MainDataViewSet(ModelViewSet):
    queryset = Main_data.objects.all()
    serializer_class = MainDataSerializer
    permission_classes = [IsAuthenticated, IsCoachOrOwner]
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['date', 'user__username']
    ordering_fields = ['date']
    ordering = ['-date']

    def perform_create(self, serializer):
        user = User.objects.get(username=self.request.data["username"])

        return serializer.save(user=user)
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()  # fetch the object
            self.perform_destroy(instance)  # delete it
            return Response({"detail": "Deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Main_data.DoesNotExist:
            # Already deleted
            return Response({"detail": "Entry does not exist."}, status=status.HTTP_404_NOT_FOUND)

class WUDViewSet(_MainDataViewSet):
    queryset = Main_data.objects.all().filter(data_collection='wellness')

class PTDViewSet(_MainDataViewSet):
    queryset = Main_data.objects.all().filter(data_collection='training')
    
class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'username'
    filter_backends = [DjangoFilterBackend]
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated, IsOwner]
        return [AllowAny]

class AthleteViewSet(UserViewSet):
    queryset = User.objects.filter(groups__name='athletes')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsCoachOrOwner]
    lookup_field = 'username'
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['username', 'first_name', 'last_name', 'email', 'is_active']

class CoachViewSet(UserViewSet):
    queryset = User.objects.filter(groups__name='coaches')
    permission_classes = [IsAuthenticated, IsCoach]
    filterset_fields = ['username', 'first_name', 'last_name', 'email', 'is_active', 'is_staff']

class AdminViewSet(UserViewSet):
    queryset = User.objects.filter(is_superuser=True)
    permission_classes = [IsAuthenticated, IsAdmin]
    filterset_fields = ['username', 'first_name', 'last_name', 'email', 'is_active', 'is_staff']

class ProfileViewSet(ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated, IsCoachOrOwner]
    lookup_field = 'user__username'

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class= MyTokenObtainPairSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_lnrmssdData(request, username):
    if User.objects.filter(username=username).exists():
        user = User.objects.filter(username=username).first()
        if not user.groups.filter(name='athletes').exists():
            return Response({'error': 'User is not an athlete'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    query = Main_data.objects.filter(user=user, data_collection='wellness').values('date', 'data').all()

    if not query.exists():
        return Response({'error': 'No data'}, status=status.HTTP_404_NOT_FOUND)

    dates= list(query.values_list('date', flat=True))

    hr= np.array([obj['data']['HR'] for obj in query]).flatten()

    rmssd= np.array([obj['data']['RMSSD'] for obj in query]).flatten()
    
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
def get_ssData(request,username):
    if User.objects.filter(username=username).exists():
        user = User.objects.filter(username=username).first()
        if not user.groups.filter(name='athletes').exists():
            return Response({'error': 'User is not an athlete'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    query = Main_data.objects.filter(user=user, data_collection='wellness').values('date', 'data').all()

    if not query.exists():
        return Response({'error': 'No data'}, status=status.HTTP_404_NOT_FOUND)

    dates= list(query.values_list('date', flat=True))

    rmssd= np.array([obj['data']['RMSSD'] for obj in query]).flatten()
    sdnn= np.array([obj['data']['SDNN'] for obj in query]).flatten()

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
    username = request.GET.get('username')
    date = request.GET.get('date')
    if not username:
        return Response({'error': 'Username parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        if User.objects.filter(username=username).exists():
            user = User.objects.filter(username=username).first()
            if not user.groups.filter(name='athletes').exists():
                Response({'error': 'User is not an athlete'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    query = Main_data.objects.filter(user=user, data_collection='wellness').values('date', 'data').all()

    if date:
        dateobj = datetime.date.fromisoformat(date)
        data = query.filter(date=dateobj).values('date', 'data__hours_of_sleep', 'data__emotional_wellness', 'data__quality_of_sleep', 'data__tiredness', 'data__comments', 'data__menstruation', 'data__muscle_pain', 'data__chispa').order_by('-date').first()
    else:
        data = query.all().values('date', 'data__hours_of_sleep', 'data__emotional_wellness', 'data__quality_of_sleep', 'data__tiredness', 'data__comments', 'data__menstruation', 'data__muscle_pain', 'data__chispa').order_by('-date').first()

    if not data:
        return Response({'error': 'No data'}, status=status.HTTP_404_NOT_FOUND)
    
    graph_data={'date':data['date'].strftime('%Y-%m-%d'), 'h_sleep':data['data__hours_of_sleep'], 'wellness':data['data__emotional_wellness'], 'q_sleep':data['data__quality_of_sleep'], 'recovery':data['data__tiredness'], 'comments':data['data__comments'], 'menstruation':data['data__menstruation'], 'pain':data['data__muscle_pain'], 'chispa':data['data__chispa']}
    return Response({'athleteUserName':username, 'graph_data':graph_data})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_rpe2XtimeData(request, username):
    if User.objects.filter(username=username).exists():
        user = User.objects.filter(username=username).first()
        if not user.groups.filter(name='athletes').exists():
            return Response({'error': 'User is not an athlete'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    data = Main_data.objects.filter(user=user, data_collection='training').values('date', 'data__perceived_strain_of_activity', 'data__time_of_activity', 'data__type_of_activity')

    if not data.exists():
        return Response({'error': 'No data'}, status=status.HTTP_404_NOT_FOUND)
    
    dates= list(data.values_list('date', flat=True))

    rpe= np.array(list(data.values_list('data__perceived_strain_of_activity'))).flatten()

    time= np.array(list(data.values_list('data__time_of_activity'))).flatten()

    rpe2Xtime=  rpe * rpe * time

    activity= np.array(list(data.values_list('data__type_of_activity'))).flatten()

    graph_data = {dates[i].strftime('%Y-%m-%d %H:%M'): {'rpe2Xtime': rpe2Xtime[i], 'activity':activity[i]} for i in range(len(dates))}

    return Response({'athleteUserName':username, 'graph_data':graph_data})

# @api_view(['get'])
# @permission_classes([IsAuthenticated])
# def get_lastWeeksTrainings(request):
#     user = request.user

#     date_str = request.data.get('date')
#     if date_str:
#         date= datetime.date.fromisoformat(date_str)
#     else:
#         date= datetime.date.today()

#     if user.groups.filter(name='athletes').exists():
#         username = user.username
#     else:
#         username= request.data.get('athleteUserName')
#         user = User.objects.filter(username=username).first()

#     data = Post_Training_Data.objects.filter(user=user, date__gte= date-datetime.timedelta(days=7), date__lte= date).values('date', 'type_of_activity', 'time_of_activity').all()
    
#     if not data.exists():
#         return Response({'error': 'No data'}, status=status.HTTP_404_NOT_FOUND)

#     dates= list(data.values_list('date', flat=True))

#     time= np.array(list(data.values_list('time_of_activity'))).flatten()

#     activity= np.array(list(data.values_list('type_of_activity'))).flatten()

#     graph_data = {dates[i].strftime('%Y-%m-%d %H:%M'): {'activity':activity[i], 'duration':time[i]} for i in range(len(dates))}

#     return Response({'athleteUserName':username, 'graph_data':graph_data})

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