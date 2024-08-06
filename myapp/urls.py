from django.urls import path
from .views import UserCreate, ChatView

urlpatterns = [
    path('users/', UserCreate.as_view(), name='user_create'),
    path('chat/', ChatView.as_view(), name='chat'),
]