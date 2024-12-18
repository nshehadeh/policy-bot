from django.urls import path
from .views import (
    UserCreate,
    ChatView,
    LoadPreviousChatView,
    UserSettingsView,
    ChatSessionView,
    DocumentSearchView,
)

urlpatterns = [
    path("users/", UserCreate.as_view(), name="user_create"),
    path(
        "user_settings/", UserSettingsView.as_view(), name="user_details"
    ),  # Endpoint for user details and settings
    path("chat/new/", ChatView.as_view(), name="chat/new"),
    path(
        "chat/sessions/", LoadPreviousChatView.as_view(), name="chat_sessions"
    ),  # Fetch all sessions
    path(
        "chat/load/", LoadPreviousChatView.as_view(), name="load_chat"
    ),  # Load a specific session's chat history
    path(
        "chat/sessions/<uuid:session_id>/",
        ChatSessionView.as_view(),
        name="chat-session-detail",
    ),
    path(
        "search/", DocumentSearchView.as_view(), name="document_search"
    ),  # Document search endpoint
]
