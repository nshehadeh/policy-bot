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
       