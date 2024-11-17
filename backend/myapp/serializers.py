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
    Serializer for handling chat messages in a streaming context.

    Attributes:
        message (CharField): The user message, optional for input.
        session_id (UUIDField): The session ID, optional for input.
        response (CharField): The AI response, read-only, used for non-streaming responses.
        is_streaming (BooleanField): Indicates if the response is streamed, read-only.
    """

    # Input fields
    message = serializers.CharField(required=False, write_only=True)
    session_id = serializers.UUIDField(required=False)

    # Output fields
    response = serializers.CharField(read_only=True)

    def validate(self, data):
        """
        Check that at least one of message or session_id is provided.
        """
        if not data.get('message') and not data.get('session_id'):
            raise serializers.ValidationError("Either 'message' or 'session_id' must be provided.")
        return data

class ChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = ['session_id', 'created_at', 'name']

class ChatSessionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = ['name']