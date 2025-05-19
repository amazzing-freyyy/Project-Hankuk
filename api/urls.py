from django.urls import path
from .views import *

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('tables/', PostTableView.as_view(), name='table-create'),
    path('data/', PostDataView.as_view(), name='submit-data'),
    path('data/update/', UpdateDataView.as_view(), name='update-data'),
    path('tables/<str:title>/structure/', GetTableStructureView.as_view(), name='get-table-structure'),
    path('tables/<str:title>/data/', GetTableDataView.as_view(), name='get-data'),
    path('tables/process/', ProcessDataView.as_view(), name='process-data'),
]