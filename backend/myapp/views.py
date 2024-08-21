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
    """
    View for creating a new user.

    Inherits from Django's generic CreateAPIView.

    Attributes:
        queryset (QuerySet): All User objects.
        serializer_class (Serializer): The serializer class used for user creation.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


class ChatView(APIView):
    """
    View for handling chat interactions.

    Handles incoming chat messages, creates or retrieves chat sessions, 
    and processes user queries using the RAGSystem.

    Attributes:
        permission_classes (list): A list of permission classes, ensuring the user is authenticated.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests to process a chat message.

        Validates the incoming chat message, creates or retrieves a chat session, 
        processes the message using RAGSystem, and stores the conversation in the database.

        Args:
            request (HttpRequest): The HTTP request object containing the chat message data.

        Returns:
            Response: A Response object containing the processed message, AI response, and session ID.
        """
        serializer = ChatMessageSerializer(data=request.data)
        
        if serializer.is_valid():
            user_message = serializer.validated_data.get('message')
            session_id = serializer.validated_data.get('session_id')
            
            if session_id:
                chat_session = ChatSession.objects.get(session_id=session_id, user=request.user)
            else:
                chat_session = ChatSession.objects.create(user=request.user)
                print("Creating new chat session, id: " + str(chat_session.session_id))
            
            if not user_message:
                return Response({'session_id': chat_session.session_id}, status=status.HTTP_201_CREATED)

            try:
                rag_system = RAGSystem()
                response = rag_system.handle_query(user_message)
                
                ChatMessage.objects.create(session=chat_session, role='human', content=user_message)
                ChatMessage.objects.create(session=chat_session, role='ai', content=response)
                                
                return Response({'message': user_message, 'response': response, 'session_id': chat_session.session_id})
            except TypeError as e:
                print(f"TypeError: {e}")
                return Response({'error': 'An error occurred while processing your request.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoadPreviousChatView(APIView):
    """
    View for loading previous chat sessions.

    Retrieves chat sessions and their histories for the authenticated user.

    Attributes:
        permission_classes (list): A list of permission classes, ensuring the user is authenticated.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests to retrieve all previous chat sessions.

        Fetches chat sessions for the authenticated user, ordered by the creation date.

        Args:
            request (HttpRequest): The HTTP request object.

        Returns:
            Response: A Response object containing serialized chat session data.
        """
        chat_sessions = ChatSession.objects.filter(user=request.user).order_by('-created_at')
        serializer = LoadPreviousChatSerializer(chat_sessions, many=True)
        return Response(serializer.data)
    
    def post(self, request, *args, **kwargs):
        """
        Handles POST requests to load a specific chat session's history.

        Loads chat messages for the specified session, reconstitutes the chat history 
        in the RAGSystem's memory, and returns the chat history.

        Args:
            request (HttpRequest): The HTTP request object containing the session ID.

        Returns:
            Response: A Response object containing the session ID and chat history, 
            or an error message if the session is not found or the session ID is missing.
        """
        session_id = request.data.get('session_id')
        
        if session_id:
            try:
                chat_session = ChatSession.objects.get(session_id=session_id, user=request.user)
                chat_session.save()
                
                chat_history = ChatMessage.objects.filter(session=chat_session).order_by('created_at')
                
                rag_system = RAGSystem()
                history = ChatMessageHistory()

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
    """
    View for managing user settings.

    Retrieves or updates the user's profile settings.

    Attributes:
        permission_classes (list): A list of permission classes, ensuring the user is authenticated.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests to retrieve the user's profile settings.

        Fetches the user's profile details (first name, last name, email, username).

        Args:
            request (HttpRequest): The HTTP request object.

        Returns:
            Response: A Response object containing the user's profile details.
        """
        user = request.user
        return Response({
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'username': user.username,
        })
        
    def post(self, request, *args, **kwargs):
        """
        Handles POST requests to update the user's profile settings.

        Validates and updates the user's profile settings based on the provided data.

        Args:
            request (HttpRequest): The HTTP request object containing the updated profile data.

        Returns:
            Response: A Response object indicating the status of the update and the updated fields,
            or an error message if validation fails.
        """
        user = request.user
        serializer = UpdateSettingsSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'settings updated', 'updated_fields': serializer.data})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
