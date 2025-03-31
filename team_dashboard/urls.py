from django.urls import path
from team_dashboard.views import *
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # path("admin/", admin.site.urls), 
    path("api/login/", TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path("api/refresh/", TokenRefreshView.as_view(), name='token_refresh'),
    path("api/protected/", protected_view, name='protected'),
    path("api/wake_up_data/", get_wakeUpData, name='get_wake_up'),
    path("api/post_training_data/", get_postTrainingData, name='get_post_training'),
    path('api/signup/', register_user, name='register'),
]  
