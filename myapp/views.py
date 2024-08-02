from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserSerializer, ChatMessageSerializer
from .rag_system import RAGSystem
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics

class UserCreate(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
class ChatView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = ChatMessageSerializer(data=request.data)
        if serializer.is_valid():
            user_message = serializer.validated_data['message']
            response = RAGSystem.handle_query(user_message)
            return Response({'message': user_message, 'response': response})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

