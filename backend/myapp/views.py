from django.shortcuts import render
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ChatMessageSerializer, ChatSessionSerializer, ChatSessionUpdateSerializer, UserSerializer, UpdateSettingsSerializer
from .rag_system import RAGSystem
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from .models import ChatSession, ChatMessage
from django.contrib.auth.models import User
from langchain.memory import ChatMessageHistory
from django.shortcuts import get_object_or_404
import json
from pymongo import MongoClient
from django.conf import settings


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
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChatMessageSerializer(data=request.data)
        
        if serializer.is_valid():
            message = serializer.validated_data.get('message', "")
        
        chat_session = ChatSession.objects.create(user=request.user)
        session_id = chat_session.session_id
        print("Creating new chat session, id: " + str(session_id) + "for: " + str(request.user))
            
        return Response({"session_id": session_id}, status=status.HTTP_200_OK)

class ChatSessionView(APIView):
    
    permission_classes = [IsAuthenticated]
    
    # Update chat name
    def patch(self, request, session_id, *args, **kwargs):
        
        session = get_object_or_404(ChatSession, session_id=session_id, user=request.user)
        serializer = ChatSessionUpdateSerializer(session, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, session_id, *args, **kwargs):
        """Delete chat session"""
        session = get_object_or_404(ChatSession, session_id=session_id, user=request.user)
        session.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    
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
        serializer = ChatSessionSerializer(chat_sessions, many=True)
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


class DocumentSearchView(APIView):
    """
    View for searching documents stored in MongoDB using RAG system.
    Returns most recent documents if no query is provided,
    or most relevant documents based on similarity search if query exists.
    """
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize MongoDB connection
        self.client = MongoClient(settings.MONGODB_URI)
        self.db = self.client[settings.MONGODB_NAME]
        # Adjust collection name as needed
        self.collection = self.db['test'] 

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests for document search.
        Uses RAG system for similarity search and fetches document details from MongoDB.
        """
        query = request.query_params.get('query', '')
        
        try:
            if query:
                # Use RAG system for similarity search
                rag_system = RAGSystem()
                # Get document IDs from RAG system
                doc_ids = rag_system.handle_search_query(query)
                
                # Get document details from MongoDB using the IDs
                documents = list(self.collection.find(
                    {'document_id': {'$in': doc_ids}},
                    {
                        'document_id': 1,
                        'title': 1, 
                        'summary': 1, 
                        'url': 1,
                        'publication_date': 1
                    }
                ))
                
                # Sort documents to match the order of doc_ids
                doc_map = {doc['document_id']: doc for doc in documents}
                documents = [doc_map[doc_id] for doc_id in doc_ids if doc_id in doc_map]
            else:
                # If no query, return most recent documents from MongoDB
                documents = list(self.collection.find(
                    {},
                    {
                        'document_id': 1,
                        'title': 1, 
                        'summary': 1, 
                        'url': 1,
                        'publication_date': 1,
                        'processed_at': 1
                    }
                ).sort('processed_at', -1).limit(6))

            # Format the response
            results = [{
                'id': doc['document_id'],
                'title': doc['title'],
                'summary': doc['summary'],
                'url': doc['url'],
                'created_at': doc['created_at'].isoformat() if 'created_at' in doc else None
            } for doc in documents]

            return Response({
                'query': query,
                'results': results
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)