from django.urls import path, include
from team_dashboard.views import *
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'wake_up', WUDViewSet, basename='wake_up_data')
router.register(r'post_training', PTDViewSet, basename='post_training')
router.register(r'athletes', AthleteViewSet, basename='athletes')
router.register(r'coaches', CoachViewSet, basename='coaches')
router.register(r'admins', AdminViewSet, basename='admins')
router.register(r'users', UserViewSet, basename='users')
router.register(r'groups', GroupViewSet, basename='groups')

urlpatterns = [
    # path("admin/", admin.site.urls), 
    path("api/login/", MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path("api/refresh/", TokenRefreshView.as_view(), name='token_refresh'),
    path('api/post_training/workload/<str:username>/', get_rpe2XtimeData, name='get_workload'),
    path('api/wake_up/lnrmssd/<str:username>/', get_lnrmssdData, name='get_lnrmssd'),
    path('api/wake_up/ss/<str:username>/', get_ssData, name='get_ss'),
    path('api/wake_up/wellness/', get_wellnessData, name='get_Wellness'),
    path('api/', include(router.urls)),
]  
