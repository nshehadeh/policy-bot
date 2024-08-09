from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserSerializer, ChatMessageSerializer, ChatHistorySerializer, UserSettingsSerializer
from .rag_system import RAGSystem
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from .models import ChatHistory, UserSettings


class UserCreate(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    

class ChatView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = ChatMessageSerializer(data=request.data)
        if serializer.is_valid():
            user_message = serializer.validated_data['message']
            print(f"User query: {user_message}")
            try:
                rag_system = RAGSystem()
                response = rag_system.handle_query(user_message)
                
                # Save chat history
                chat_history = ChatHistory(
                    user=request.user,
                    message=user_message,
                    response=response
                )
                chat_history.save()
                
                return Response({'message': user_message, 'response': response})
            except TypeError as e:
                print(f"TypeError: {e}")
                return Response({'error': 'An error occurred while processing your request.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        settings = UserSettings.objects.filter(user=request.user)
        serializer = UserSettingsSerializer(settings, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = UserSettingsSerializer(data=request.data)
        if serializer.is_valid():
            setting = serializer.save(user=request.user)
            return Response(UserSettingsSerializer(setting).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)