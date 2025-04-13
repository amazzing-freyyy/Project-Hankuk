from django.urls import re_path
from team_dashboard.consumers import *

websocket_urlpatterns = [
    re_path(r'ws/test/$', TestConsumer.as_asgi()),
    re_path(r'ws/newWUD/$', NewWUD.as_asgi()),
    re_path(r'ws/alert/$', Alert.as_asgi()),
]