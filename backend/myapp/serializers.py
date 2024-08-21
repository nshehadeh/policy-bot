from rest_framework import serializers
from django.contrib.auth.models import User
from .models import ChatSession

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and managing User instances.

    Meta:
        model (Model): The User model that this serializer maps to.
        fields (tuple): The fields to include in the serialization.
        extra_kwargs (dict): Extra keyword arguments for specific fields (e.g., making the password write-only).
    """

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'password')
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        """
        Creates a new User instance with the validated data.

        Args:
            validated_data (dict): The validated data from the serializer.

        Returns:
            User: The created User instance.
        """
        user = User.objects.create_user(**validated_data)
        return user

class UpdateSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for updating User profile settings.

    Meta:
        model (Model): The User model that this serializer maps to.
        fields (list): The fields to include in the serialization, specifically for updating first and last name.
    """

    class Meta:
        model = User
        fields = ['first_name', 'last_name']

class ChatMessageSerializer(serializers.Serializer):
    """
    Serializer for handling chat messages.

    Attributes:
        message (CharField): The user message, optional.
        response (CharField): The AI response, read-only.
        session_id (UUIDField): The session ID, optional.
    """

    message = serializers.CharField(required=False)
    response = serializers.CharField(read_only=True)
    session_id = serializers.UUIDField(required=False)

class LoadPreviousChatSerializer(serializers.ModelSerializer):
    """
    Serializer for loading previous chat sessions.

    Meta:
        model (Model): The ChatSession model that this serializer maps to.
        fields (list): The fields to include in the serialization, limited to session ID and creation time.
    """

    class Meta:
        model = ChatSession
        fields = ['session_id', 'created_at']  # Only expose session ID and creation time
