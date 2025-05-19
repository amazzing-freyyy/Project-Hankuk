from django.urls import path
from .views import *

urlpatterns = [
    path('signup/', SignupView.as_view()),
    path('token/', CustomTokenObtainPairView.as_view()),
    path('token/refresh/', CustomTokenRefreshView.as_view()),
    path('tables/', PostTableView.as_view()),
    path('data/', PostDataView.as_view()),
    path('data/update/', UpdateDataView.as_view()),
    path('tables/<str:title>/structure/', GetTableStructureView.as_view()),
    path('tables/<str:title>/data/', GetTableDataView.as_view()),
    path('tables/process/', ProcessDataView.as_view()),
]