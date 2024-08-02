from django.urls import path
from .views import UserCreate, ChatView

urlpatterns = [
    path('api/users/', UserCreate.as_view(), name='user_create'),
    path('api/chat/', ChatView.as_view(), name='chat'),
]