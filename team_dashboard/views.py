from django.http.response import HttpResponse as HttpResponse
from django.contrib.auth.models import User, Group
import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
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
from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

logger = logging.getLogger(__name__) 

class _MainDataViewSet(ModelViewSet):
    queryset = Main_data.objects.all()
    serializer_class = MainDataSerializer
    permission_classes = [IsAuthenticated, IsCoach | IsOwner | IsAdmin]
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
    queryset = Main_data.objects.filter(data_collection='wellness')

class PTDViewSet(_MainDataViewSet):
    queryset = Main_data.objects.all().filter(data_collection='training')

class GroupViewSet(ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    lookup_field = 'name'
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name']

class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'username'
    filter_backends = [DjangoFilterBackend]

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminOrOwner()]
        return [AllowAny()]

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOwner | IsAdmin])
    def change_password(self, request, username=None):
        user = self.get_object()
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if request.user.groups.filter(name='coaching_staff').exists():
            if not new_password:
                return Response({"detail": "No password given"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            if not old_password or not new_password:
                return Response({"detail": "Old and new passwords are required."}, status=status.HTTP_400_BAD_REQUEST)
            if not user.check_password(old_password):
                return Response({"detail": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response({"detail": list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({"detail": "Password changed successfully."}, status=status.HTTP_200_OK)
    
class AthleteViewSet(UserViewSet):
    queryset = User.objects.filter(groups__name='athletes')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsCoach | IsOwner | IsAdmin]
    lookup_field = 'username'
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['username', 'first_name', 'last_name', 'email', 'is_active']

class CoachViewSet(UserViewSet):
    queryset = User.objects.filter(groups__name='coaches')
    permission_classes = [IsAuthenticated, IsCoach | IsAdmin]
    filterset_fields = ['username', 'first_name', 'last_name', 'email', 'is_active', 'is_staff']

class AdminViewSet(UserViewSet):
    queryset = User.objects.filter(is_superuser=True)
    permission_classes = [IsAuthenticated, IsAdmin]
    filterset_fields = ['username', 'first_name', 'last_name', 'email', 'is_active', 'is_staff']

class ProfileViewSet(ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated, IsCoach | IsOwner | IsAdmin]
    lookup_field = 'user__username'

class UploadProfileImage(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, username):
        user = get_object_or_404(User, username=username)
        user.profile.avatar = request.FILES['image']
        user.profile.save()
        return Response({'image_url': user.profile.avatar.url})

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

    query = Main_data.objects.filter(user=user, data_collection='wellness').values('date', 'data').all().order_by('date')

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

    query = Main_data.objects.filter(user=user, data_collection='wellness').values('date', 'data').all().order_by('date')

    if not query.exists():
        return Response({'error': 'No data'}, status=status.HTTP_404_NOT_FOUND)

    dates= list(query.values_list('date', flat=True))

    rmssd= np.array([obj['data']['RMSSD'] for obj in query]).flatten()
    sdnn= np.array([obj['data']['SDNN'] for obj in query]).flatten()

    ss= 1000 / (sdnn / 0.7995) + 5.1174
    sp= ss / (0.7071 * rmssd)
    ss = np.where(~np.isfinite(ss), np.nan, ss)
    sp = np.where(~np.isfinite(sp), np.nan, sp)

    # --- Compute z-score ---
    interval = 7
    if len(ss) >= interval:
        windows = sliding_window_view(ss, window_shape=interval)
        means = np.nanmean(windows, axis=1)
        stds = np.nanstd(windows, axis=1)
        target_val = ss[interval - 1:]
        z_score = (target_val - means) / stds

        # Replace inf/nan in z_score
        z_score = np.where(~np.isfinite(z_score), np.nan, z_score)

        p_len = interval - 1
        p_z_score = np.concatenate([np.full(p_len, np.nan), z_score])
    else:
        # Not enough data for sliding window
        p_z_score = np.full(len(ss), np.nan)

    # --- Convert np.nan to None for JSON compatibility ---
    def safe_value(val):
        if isinstance(val, (np.floating, float)) and (np.isnan(val) or not np.isfinite(val)):
            return 0
        return float(val) if isinstance(val, (np.floating, float)) else val

    graph_data = {
        dates[i].strftime('%Y-%m-%d'): {
            'ss': safe_value(ss[i]),
            'sp': safe_value(sp[i]),
            'ss_z_score': safe_value(p_z_score[i]),
        }
        for i in range(len(dates))
    }

    return Response({'athleteUserName': username, 'graph_data': graph_data})

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

    query = Main_data.objects.filter(user=user, data_collection='wellness').values('date', 'data').all().order_by('-date')

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

    data = Main_data.objects.filter(user=user, data_collection='training').values('date', 'data__perceived_strain_of_activity', 'data__time_of_activity', 'data__type_of_activity').order_by('-date')

    if not data.exists():
        return Response({'error': 'No data'}, status=status.HTTP_404_NOT_FOUND)
    
    dates= list(data.values_list('date', flat=True))

    rpe= np.array(list(data.values_list('data__perceived_strain_of_activity'))).flatten()

    time= np.array(list(data.values_list('data__time_of_activity'))).flatten()

    rpe2Xtime=  rpe * rpe * time

    activity= np.array(list(data.values_list('data__type_of_activity'))).flatten()

    graph_data = {dates[i].strftime('%Y-%m-%d %H:%M'): {'rpe2Xtime': rpe2Xtime[i], 'activity':activity[i]} for i in range(len(dates))}

    return Response({'athleteUserName':username, 'graph_data':graph_data})

def clean_infinite_values(data):
    if isinstance(data, dict):
        return {k: clean_infinite_values(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_infinite_values(v) for v in data]
    elif isinstance(data, (float, np.floating)):
        if np.isnan(data) or np.isinf(data):
            return 'Nan'  # or 0.0, depending on what makes sense for your API
        return float(data)
    else:
        return data
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

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def users_in_group(request, group_name):
#     try:
#         group = Group.objects.get(name=group_name)
#     except Group.DoesNotExist:
#         return Response({'error': 'Group not found'}, status=status.HTTP_404_NOT_FOUND)

#     users = group.user_set.all()
#     serializer = UserSerializer(users, many=True)
#     return Response(serializer.data)