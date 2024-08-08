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
            