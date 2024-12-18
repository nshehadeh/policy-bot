"""
Database models

This module defines the database schema for chat-related functionality,
including chat sessions and messages.
"""

from django.db import models
from django.contrib.auth.models import User
import uuid
from django.utils import timezone


class ChatSession(models.Model):
    """
    Represents a chat conversation between a user and the AI.

    Each session contains multiple messages and maintains its own context.
    Sessions are uniquely identified by UUID and can be named for easier reference.

    Attributes:
        user (User): The user who owns this chat session
        session_id (UUID): Unique identifier for the session
        created_at (datetime): When the session was created
        name (str): Optional display name for the session

    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="chat_sessions",
    )
    session_id = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        """
        Saves the chat session, setting a default name if none provided.

        The default name format is 'Chat on YYYY-MM-DD @ HH:MM'.

        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        if not self.name:
            self.name = f"Chat on {timezone.now().strftime('%Y-%m-%d @ %H:%M')}"
        super().save(*args, **kwargs)

    def __str__(self):
        """
        Returns a string representation of the chat session.

        Format: "Session <uuid> for <username>"

        Returns:
            str: Human-readable identifier for this session
        """
        return f"Session {self.session_id} for {self.user.username}"


class ChatMessage(models.Model):
    """
    Represents a single message within a chat session.

    Messages can be from either the human user or the AI system.
    Each message is timestamped and belongs to a specific chat session.

    Attributes:
        session (ChatSession): The session this message belongs to
        role (str): Who sent the message ('human' or 'ai')
        content (str): The actual message text
        created_at (datetime): When the message was sent
    """

    ROLE_CHOICES = [("human", "Human"), ("ai", "AI")]

    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """
        Returns a string representation of the message.

        Format: "Message by <role> at <timestamp>"

        Returns:
            str: Human-readable identifier for this message
        """
        return f"Message by {self.role} at {self.created_at}"
