from django.urls import path, include
from team_dashboard.views import *
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'wake_up', WUDViewSet, basename='wake_up_data')
router.register(r'post_training', PTDViewSet, basename='post_training')
router.register(r'user', UserViewSet, basename='user')

urlpatterns = [
    # path("admin/", admin.site.urls), 
    path("api/login/", MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path("api/refresh/", TokenRefreshView.as_view(), name='token_refresh'),
    path('api/wake_up/lnrmssd', get_lnrmssdData, name='get_lnrmssd'),
    path('api/wake_up/ss', get_ssData, name='get_ss'),
    path('api/wake_up/wellness', get_wellnessData, name='get_Wellness'),path('api/users/<str:group_name>/', users_in_group, name='users_in_group'),
    path('api/', include(router.urls)),
]  
