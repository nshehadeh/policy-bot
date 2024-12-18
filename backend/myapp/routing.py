"""
WebSocket URL routing configuration for the Policy Bot API.

This module defines WebSocket URL patterns that enable real-time communication
between clients and the server. It maps WebSocket connections to their respective
consumer classes.

URL Pattern:
    ws/chat/<session_id>/: Handles chat messages for a specific session
    - session_id: UUID identifier for the chat session
"""

from django.urls import re_path
from myapp import consumers

websocket_urlpatterns = [
    re_path(r"^ws/chat/(?P<session_id>[\w-]+)/$", consumers.ChatConsumer.as_asgi()),
]
