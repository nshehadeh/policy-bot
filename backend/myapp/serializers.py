"""
Serializers for the Policy Bot API.

This module defines the serializers used to convert complex data types to Python datatypes

Key components:
- User management serializers (creation and settings updates)
- Chat session serializers (creation, updates, and listing)
- Chat message serializer for handling streaming responses
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import ChatSession


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and managing User instances.

    This serializer handles user registration and profile management.
    The password field is write-only for security.

    Fields:
        id (int): User's unique identifier
        username (str): User's login name
        email (str): User's email address
        first_name (str): User's first name
        last_name (str): User's last name
        password (str): User's password (write-only)
    """

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "password")
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def create(self, validated_data):
        """
        Creates a new User instance with the validated data.

        Uses Django's create_user method to properly hash the password.

        Args:
            validated_data (dict): The validated data from the serializer.

        Returns:
            User: The created User instance with hashed password.
        """
        user = User.objects.create_user(**validated_data)
        return user


class UpdateSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for updating User profile settings.

    This serializer is specifically for updating user profile information,
    currently supporting first and last name updates.

    Fields:
        first_name (str): User's first name
        last_name (str): User's last name
    """

    class Meta:
        model = User
        fields = ["first_name", "last_name"]


class ChatMessageSerializer(serializers.Serializer):
    """
    Serializer for handling chat messages in a streaming context.

    This serializer handles both incoming chat messages and outgoing
    streaming responses. It supports two modes:
    1. New message mode: User sends a new message
    2. History mode: Loading previous messages by session ID

    Fields:
        message (str, optional): The user's input message
        session_id (UUID, optional): Chat session identifier
        response (str): AI system's response (read-only)

    Note:
        Either message or session_id must be provided for valid input.
    """

    # Input fields
    message = serializers.CharField(required=False, write_only=True)
    session_id = serializers.UUIDField(required=False)

    # Output fields
    response = serializers.CharField(read_only=True)

    def validate(self, data):
        """
        Validates that either message or session_id is provided.

        Args:
            data (dict): The input data to validate

        Returns:
            dict: The validated data

        Raises:
            ValidationError: If neither message nor session_id is provided
        """
        if not data.get("message") and not data.get("session_id"):
            raise serializers.ValidationError(
                "Either 'message' or 'session_id' must be provided."
            )
        return data


class ChatSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying chat session information.

    Used for listing chat sessions and showing their basic details.

    Fields:
        session_id (UUID): Unique identifier for the chat session
        created_at (datetime): When the session was created
        name (str): Display name for the chat session
    """

    class Meta:
        model = ChatSession
        fields = ["session_id", "created_at", "name"]


class ChatSessionUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating chat session details.

    Currently supports updating the display name of a chat session.

    Fields:
        name (str): New display name for the chat session
    """

    class Meta:
        model = ChatSession
        fields = ["name"]
