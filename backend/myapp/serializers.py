from rest_framework import serializers
from django.contrib.auth.models import User
from .models import ChatSession

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'password')
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
    
class ChatMessageSerializer(serializers.Serializer):
    message = serializers.CharField()
    response = serializers.CharField(read_only=True)

class UpdateSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']

class ChatMessageSerializer(serializers.Serializer):
    message = serializers.CharField()
    response = serializers.CharField(read_only=True)
    session_id = serializers.UUIDField(required=False)
    
class StartNewChatSerializer(serializers.Serializer):
    new_chat = serializers.BooleanField(default=True)
    
class LoadPreviousChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = ['session_id', 'created_at']  # Only expose session ID and creation time

     
