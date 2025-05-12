from django.urls import path
from team_dashboard.views import *
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # path("admin/", admin.site.urls), 
    path("api/login/", MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path("api/refresh/", TokenRefreshView.as_view(), name='token_refresh'),
    path("api/protected/", protected_view, name='protected'),
    path("api/wake_up/", get_allWakeUpData, name='get_wake_up'),
    path('api/wake_up/lnrmssd', get_lnrmssdData, name='get_lnrmssd'),
    path('api/wake_up/ss', get_ssData, name='get_ss'),
    path('api/wake_up/wellness', get_wellnessData, name='get_Wellness'),
    path('api/wake_up/new', new_WUD, name='new_WUD'),
    path('api/wake_up/<slug:slug>/update', update_WUD, name='update_WUD'),
    path("api/post_training/", get_allPostTrainingData, name='get_post_training'),
    path("api/post_training/rpe2Xtime", get_rpe2XtimeData, name='get_rpe2Xtime'),
    path("api/post_training/PT", get_PTData, name='get_PT'),
    path('api/post_training/new', new_PT, name='new_PT'),
    path('api/post_training/<slug:slug>/update', update_PT, name='update_PT'),
    path('api/post_training/<slug:slug>/delete', delete_PT, name='delete_PT'),
    path("api/post_training/latestactivities", get_lastWeeksTrainings, name='get_lastWeeksTrainings'),
    path('api/signup/', register_user, name='register'),
    path('user/<str:username>/update/', update_user, name='update_user'),
    path('user/<str:username>/delete/', delete_user, name='delete_user'),
]  
