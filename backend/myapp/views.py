from django.shortcuts import render
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ChatMessageSerializer, StartNewChatSerializer, LoadPreviousChatSerializer, UserSerializer
from .rag_system import RAGSystem
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from .models import ChatSession, ChatMessage
from django.contrib.auth.models import User



class UserCreate(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

"""
class StartNewChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = StartNewChatSerializer(data=request.data)
        if serializer.is_valid() and serializer.validated_data['new_chat']:
            # Create a new chat session
            chat_session = ChatSession.objects.create(user=request.user)
            return Response({'session_id': str(chat_session.session_id)}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  
"""


class ChatView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = ChatMessageSerializer(data=request.data)
        if serializer.is_valid():
            user_message = serializer.validated_data['message']
            session_id = serializer.validated_data.get('session_id')
            
            if session_id:
                chat_session = ChatSession.objects.get(session_id=session_id, user=request.user)
            else:
                chat_session = ChatSession.objects.create(user=request.user)
            
            try:
                rag_system = RAGSystem()                
                response = rag_system.handle_query(user_message)
                 # Chat history for the current chat is saved from within the RAGSystem class (through Langchain ChatTemplateHistory)
                 # Save user message and AI response to the chat history in the database
                ChatMessage.objects.create(session=chat_session, role='human', content=user_message)
                ChatMessage.objects.create(session=chat_session, role='ai', content=response)
                                
                return Response({'message': user_message, 'response': response})
            except TypeError as e:
                print(f"TypeError: {e}")
                return Response({'error': 'An error occurred while processing your request.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class LoadPreviousChatView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        chat_sessions = ChatSession.objects.filter(user=request.user).order_by('-created_at')
        serializer = LoadPreviousChatSerializer(chat_sessions, many=True)
        return Response(serializer.data)
    
    def post(self, request, *args, **kwargs):
        session_id = request.data.get('session_id')
        if session_id:
            try:
                chat_session = ChatSession.objects.get(session_id=session_id, user=request.user)
                chat_history = ChatMessage.objects.filter(session=chat_session).order_by('created_at')
                rag_system = RAGSystem()
                rag_system.load_memory(chat_history)
                
                return Response({'session_id': str(chat_session.session_id)}, status=status.HTTP_200_OK)
            except ChatSession.DoesNotExist:
                return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'error': 'Session ID is required'}, status=status.HTTP_400_BAD_REQUEST)

    
    
class UserSettingsView(APIView):
    permission_classes = [IsAuthenticated]
    """
    def get(self, request, *args, **kwargs):
        settings = UserSettings.objects.filter(user=request.user)
        serializer = UserSettingsSerializer(settings, many=True)
        return Response(serializer.data)
    """
    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = UpdateSettingsSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'settings updated', 'updated_fields': serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)