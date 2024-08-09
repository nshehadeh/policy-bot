from .models import CustomUser
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'password', 'chat_history')
        extra_kwargs = {
            'password': {'write_only': True},
            'chat_history': {'read_only': True}  # Chat history is read-only
        }

    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        return user
#TODO Do I need response here?
class ChatMessageSerializer(serializers.Serializer):
    message = serializers.CharField()
    response = serializers.CharField(read_only=True)

"""class ChatHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['user', 'message', 'response', 'timestamp']
"""
class UpdateSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name']
        # read_only_fields = ['user']