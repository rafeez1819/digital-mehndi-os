from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/emotion/(?P<user_id>[^/]+)/$', consumers.EmotionStreamConsumer.as_asgi()),
    re_path(r'ws/emotion/$', consumers.EmotionStreamConsumer.as_asgi()),
]
