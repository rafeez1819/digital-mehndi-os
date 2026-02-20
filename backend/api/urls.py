from django.urls import path
from . import views

urlpatterns = [
    path('health/',                views.HealthView.as_view(),          name='health'),
    path('emotion/process/',       views.ProcessEmotionView.as_view(),  name='process'),
    path('emotion/history/',       views.EmotionHistoryView.as_view(),  name='history'),
    path('profile/<str:user_id>/', views.EmotionalProfileView.as_view(), name='profile'),
]
