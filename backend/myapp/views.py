from django.shortcuts import render
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ChatMessageSerializer, LoadPreviousChatSerializer, UserSerializer, UpdateSettingsSerializer
from .rag_system import RAGSystem
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from .models import ChatSession, ChatMessage
from django.contrib.auth.models import User
from langchain.memory import ChatMessageHistory



class UserCreate(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class ChatView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = ChatMessageSerializer(data=request.data)
        if serializer.is_valid():
            user_message = serializer.validated_data.get('message')
            session_id = serializer.validated_data.get('session_id')
            
            if session_id:
                chat_session = ChatSession.objects.get(session_id=session_id, user=request.user)
            else:
                chat_session = ChatSession.objects.create(user=request.user)
                print("Creating new chat session, id: " + str(chat_session.session_id))
            
            # If there's no user_message, simply return the session_id without processing a message
            if not user_message:
                return Response({'session_id': chat_session.session_id}, status=status.HTTP_201_CREATED)
            try:
                rag_system = RAGSystem()                
                response = rag_system.handle_query(user_message)
                 # Chat history for the current chat is saved from within the RAGSystem class (through Langchain ChatTemplateHistory)
                 # Save user message and AI response to the chat history in the database
                ChatMessage.objects.create(session=chat_session, role='human', content=user_message)
                ChatMessage.objects.create(session=chat_session, role='ai', content=response)
                                
                return Response({'message': user_message, 'response': response, 'session_id': chat_session.session_id})
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
                # Save adjusts the date
                chat_session.save()
                
                chat_history = ChatMessage.objects.filter(session=chat_session).order_by('created_at')
                rag_system = RAGSystem()
                print(message.content for message in chat_history)
                history = ChatMessageHistory()

                # Iterate through chat_history and add messages to ChatMessageHistory
                for message in chat_history:
                    if message.role == 'human':
                        history.add_user_message(message.content)
                    elif message.role == 'ai':
                        history.add_ai_message(message.content)

                rag_system.load_memory(history)
                
                chat_history_data = [{'role': message.role, 'content': message.content} for message in chat_history]
                
                return Response({'session_id': str(chat_session.session_id), 'chat_history': chat_history_data}, status=status.HTTP_200_OK)
            except ChatSession.DoesNotExist:
                return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'error': 'Session ID is required'}, status=status.HTTP_400_BAD_REQUEST)

    
    
class UserSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        return Response({
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'username': user.username,
        })
        
    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = UpdateSettingsSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'settings updated', 'updated_fields': serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
