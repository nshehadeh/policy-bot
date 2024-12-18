"""
URL Configuration for the Policy Bot API.

This module defines the URL routing for the Policy Bot application's REST API endpoints.
The API is organized into several functional areas:

1. User Management:
   - User creation
   - User settings

2. Chat Management:
   - Creating new chat sessions
   - Loading and managing existing sessions
   - Chat history retrieval

3. Document Search:
   - Semantic search using RAG system
   - Random document retrieval
"""

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
    # User Management Endpoints
    path("users/", 
         UserCreate.as_view(), 
         name="user_create"  # Handles user registration
    ),
    path("user_settings/", 
         UserSettingsView.as_view(), 
         name="user_details"  # Manages user preferences and settings
    ),

    # Chat Session Management Endpoints
    path("chat/new/", 
         ChatView.as_view(), 
         name="chat/new"  # Creates a new chat session
    ),
    path("chat/sessions/", 
         LoadPreviousChatView.as_view(), 
         name="chat_sessions"  # Lists all chat sessions for the user
    ),
    path("chat/load/", 
         LoadPreviousChatView.as_view(), 
         name="load_chat"  # Loads messages from a specific chat session
    ),
    path("chat/sessions/<uuid:session_id>/",
         ChatSessionView.as_view(),
         name="chat-session-detail"  # Updates or deletes specific chat sessions
    ),

    # Document Search Endpoint
    path("search/", 
         DocumentSearchView.as_view(), 
         name="document_search"  # Handles semantic search and document retrieval
    ),
]
