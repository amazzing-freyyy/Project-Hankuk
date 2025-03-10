from .forms import RememberMeForm
from django.urls import path
from team_dashboard.views import Athlete_Home, Coach_Home, WakeUpFormView, PostTrainingFormView, RedirectView, Wellness_Dashboard, profile, Login
# from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    # path("admin/", admin.site.urls), 
    path("home/", RedirectView.as_view(), name='redirect'),
    path("athlete_home/", Athlete_Home.as_view(), name='athlete_home'),
    path("coach_home/", Coach_Home.as_view(), name="coach_home"),
    path("wellness_dashboard/<str:user>", Wellness_Dashboard.as_view(), name= "wellness_dashboard"),
    path('login/', Login.as_view(authentication_form=RememberMeForm), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('wake_up_survey/', WakeUpFormView.as_view(), name='wake_up_form'),
    path('post_training_survey/', PostTrainingFormView.as_view(), name='post_training_form'),
    path('upload-avatar/', profile, name='upload_avatar'),
]  
