from django.urls import path
from .views import UserCreate, ChatView

urlpatterns = [
    path('users/', UserCreate.as_view(), name='user_create'),
    path('user_settings/', UserSettingsView.as_view(), name='user_details'),  # Endpoint for user details and settings
    path('chat/', ChatView.as_view(), name='chat'),
    path('chat/sessions/', LoadPreviousChatView.as_view(), name='chat_sessions'),  # Fetch all sessions
    path('chat/load/', LoadPreviousChatView.as_view(), name='load_chat'),  # Load a specific session's chat history
]
