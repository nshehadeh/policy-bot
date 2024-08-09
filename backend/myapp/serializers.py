from django.contrib.auth.models import User
from rest_framework import serializers
from .models import ChatHistory, UserSettings

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        username = validated_data.get('username')
        password = validated_data.get('password')

        user = User.objects.create_user(username=username, password=password)
        UserSettings.objects.create(user=user, setting_name='username', setting_value=username)
        return user

#TODO Do I need response here?
class ChatMessageSerializer(serializers.Serializer):
    message = serializers.CharField()
    response = serializers.CharField(read_only=True)

class ChatHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatHistory
        fields = ['user', 'message', 'response', 'timestamp']

class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = ['user', 'setting_name', 'setting_value']
        read_only_fields = ['user']