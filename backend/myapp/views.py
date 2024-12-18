"""
Django Views for the Policy Bot API.

This module contains the API views for handling chat sessions, user management,
document search, and user settings. It implements RESTful endpoints using Django REST Framework.

Key components:
- Chat session management (creation, updates, deletion)
- User creation and settings management
- Document search using RAG (Retrieval Augmented Generation)
- Error handling and logging
"""

from typing import List, Dict, Any
from uuid import UUID
from pymongo.mongo_client import MongoClient
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import APIException, ValidationError
from rest_framework import status
from rest_framework.request import Request
from .serializers import (
    ChatSessionSerializer,
    ChatSessionUpdateSerializer,
    UserSerializer,
    UpdateSettingsSerializer,
)
from .rag_system import RAGSystem
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from .models import ChatSession, ChatMessage
from django.contrib.auth.models import User
from bson import ObjectId
from langchain_community.chat_message_histories import ChatMessageHistory
from django.shortcuts import get_object_or_404
import json
from pymongo import MongoClient
from django.conf import settings
import os
from django.db import DatabaseError
import logging

logger = logging.getLogger(__name__)


class BaseAPIView(APIView):
    """
    Base API view with common error handling functionality.
    
    This class provides standardized error handling methods for database operations,
    validation, and unexpected errors. All API views should inherit from this class
    to maintain consistent error handling across the application.

    Methods:
        handle_database_error: Handles database-related errors
        handle_validation_error: Handles data validation errors
        handle_unexpected_error: Handles unexpected exceptions
    """

    def handle_database_error(self, e: Exception, operation: str) -> Response:
        """
        Handle database-related errors with consistent logging and response format.

        Args:
            e (Exception): The database error that occurred
            operation (str): Description of the operation that failed

        Returns:
            Response: A 500 response with error details
        """
        logger.error(f"Database error in {operation}: {str(e)}")
        return Response(
            {"error": f"Database error while {operation}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    def handle_validation_error(self, e: ValidationError, operation: str) -> Response:
        """
        Handle validation errors with consistent logging and response format.

        Args:
            e (ValidationError): The validation error that occurred
            operation (str): Description of the operation that failed

        Returns:
            Response: A 400 response with validation error details
        """
        logger.warning(f"Validation error in {operation}: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def handle_unexpected_error(self, e: Exception, operation: str) -> None:
        """
        Handle unexpected errors with logging and raise as API exception.

        Args:
            e (Exception): The unexpected error that occurred
            operation (str): Description of the operation that failed

        Raises:
            APIException: Always raised with error details
        """
        logger.error(f"Unexpected error in {operation}: {str(e)}")
        raise APIException(f"Unexpected error while {operation}")


class UserCreate(generics.CreateAPIView):
    """
    View for creating a new user.

    This view requires authentication and creates a new user, inheriting error handling and creation from Django's CreateAPIView

    Attributes:
        queryset (QuerySet): All User objects.
        serializer_class (Serializer): The serializer class used for user creation.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer


class ChatView(BaseAPIView):
    """
    View for creating new chat sessions.

    This view requires authentication and creates a new chat session
    for the authenticated user.

    Attributes:
        permission_classes (list): Requires user authentication
    """
    
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Create a new chat session for the authenticated user.

        Returns:
            Response: A 201 response with the new session ID on success,
                     or appropriate error response on failure
        """
        try:
            chat_session = ChatSession.objects.create(user=request.user)
            return Response(
                {"session_id": chat_session.session_id}, status=status.HTTP_201_CREATED
            )
        except DatabaseError as e:
            return self.handle_database_error(e, "creating new chat")
        except Exception as e:
            self.handle_unexpected_error(e, "creating new chat")


class ChatSessionView(BaseAPIView):
    """
    View for managing existing chat sessions.

    Provides endpoints for updating and deleting chat sessions.
    Only allows users to modify their own chat sessions.

    Attributes:
        permission_classes (list): Requires user authentication
    """

    permission_classes = [IsAuthenticated]

    def get_chat_session(self, session_id: UUID) -> ChatSession:
        """
        Retrieve a chat session for the current user.

        Args:
            session_id: The ID of the chat session to retrieve

        Returns:
            ChatSession: The requested chat session

        Raises:
            Http404: If the session doesn't exist or belongs to another user
        """
        return get_object_or_404(
            ChatSession, session_id=session_id, user=self.request.user
        )

    def patch(
        self, request: Request, session_id: UUID, *args: Any, **kwargs: Any
    ) -> Response:
        """
        Update a chat session's details

        Args:
            request: The HTTP request
            session_id: The ID of the chat session to update

        Returns:
            Response: Updated session data or error response
        """
        try:
            session = self.get_chat_session(session_id)
            serializer = ChatSessionUpdateSerializer(
                session, data=request.data, partial=True
            )

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except DatabaseError as e:
            return self.handle_database_error(e, "updating chat session")
        except ValidationError as e:
            return self.handle_validation_error(e, "updating chat session")
        except Exception as e:
            self.handle_unexpected_error(e, "updating chat session")

    def delete(
        self, request: Request, session_id: UUID, *args: Any, **kwargs: Any
    ) -> Response:
        """
        Delete a chat session.

        Args:
            request: The HTTP request
            session_id: The ID of the chat session to delete

        Returns:
            Response: 204 No Content on success or error response
        """
        try:
            session = self.get_chat_session(session_id)
            session.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DatabaseError as e:
            return self.handle_database_error(e, "deleting chat session")
        except Exception as e:
            self.handle_unexpected_error(e, "deleting chat session")


class LoadPreviousChatView(BaseAPIView):
    """
    View for loading and managing chat history.

    Provides endpoints for:
    - Retrieving all chat sessions for a user
    - Loading messages from a specific chat session
    - Loading chat message history for the RAG system

    Attributes:
        permission_classes (list): Requires user authentication
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Retrieve all chat sessions for the current user.

        Returns:
            Response: List of chat sessions ordered by creation date
        """
        try:
            logger.info(f"Fetching chat sessions for user: {request.user}")
            chat_sessions = ChatSession.objects.filter(user=request.user).order_by(
                "-created_at"
            )
            serializer = ChatSessionSerializer(chat_sessions, many=True)
            logger.info(f"Successfully retrieved {len(chat_sessions)} chat sessions")
            return Response(serializer.data)
        except DatabaseError as e:
            return self.handle_database_error(e, "fetching chat sessions")
        except Exception as e:
            self.handle_unexpected_error(e, "fetching chat sessions")

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Load messages from a specific chat session and load chat history.

        Args:
            request: The HTTP request containing session_id

        Returns:
            Response: Chat messages and history for the RAG system
        """
        try:
            session_id = request.data.get("session_id")
            if not session_id:
                logger.warning("Session ID not provided in request")
                return Response(
                    {"error": "Session ID is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            logger.info(f"Loading chat history for session: {session_id}")
            chat_session = get_object_or_404(
                ChatSession, session_id=session_id, user=request.user
            )
            chat_history = ChatMessage.objects.filter(session=chat_session).order_by(
                "created_at"
            )
            logger.info(f"Found {len(chat_history)} messages for session {session_id}")

            rag_system = RAGSystem()
            history = ChatMessageHistory()

            for message in chat_history:
                if message.role == "human":
                    history.add_user_message(message.content)
                elif message.role == "ai":
                    history.add_ai_message(message.content)

            logger.info(
                f"Loading chat history into RAG system for session {session_id}"
            )
            rag_system.load_memory(history)

            chat_history_data = [
                {"role": message.role, "content": message.content}
                for message in chat_history
            ]
            return Response(
                {
                    "session_id": str(chat_session.session_id),
                    "chat_history": chat_history_data,
                }
            )

        except DatabaseError as e:
            return self.handle_database_error(e, "loading chat history")
        except Exception as e:
            self.handle_unexpected_error(e, "loading chat history")


class UserSettingsView(BaseAPIView):
    """
    View for managing user settings.

    Provides endpoints for retrieving and updating user settings.

    Attributes:
        permission_classes (list): Requires user authentication
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Retrieve user settings.

        Returns:
            Response: User settings data
        """
        try:
            logger.info(f"Retrieving settings for user: {request.user.id}")
            user = request.user
            return Response(
                {
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "username": user.username,
                }
            )
        except DatabaseError as e:
            return self.handle_database_error(e, "retrieving user settings")
        except Exception as e:
            self.handle_unexpected_error(e, "retrieving user settings")

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Update user settings.

        Args:
            request: The HTTP request containing updated settings

        Returns:
            Response: Updated settings data or error response
        """
        try:
            logger.info(f"Updating settings for user: {request.user.id}")
            user = request.user
            serializer = UpdateSettingsSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            logger.info(f"Successfully updated settings for user: {request.user.id}")
            return Response(
                {"status": "settings updated", "updated_fields": serializer.data}
            )
        except ValidationError as e:
            return self.handle_validation_error(e, "updating user settings")
        except DatabaseError as e:
            return self.handle_database_error(e, "updating user settings")
        except Exception as e:
            self.handle_unexpected_error(e, "updating user settings")


class DocumentSearchView(BaseAPIView):
    """
    View for searching documents using the RAG system.

    This view provides document search functionality with the following features:
    - MongoDB integration for document storage
    - Semantic search using RAG system
    - Random document retrieval when no query is provided

    Attributes:
        permission_classes (list): Requires user authentication
    """

    permission_classes = [IsAuthenticated]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize MongoDB connection and RAG system.

        Sets up the MongoDB client, database, and collection connections
        required for document retrieval.
        """
        super().__init__(*args, **kwargs)
        self.client = None
        self.db = None
        self.collection = None
        self.initialize_mongodb()

    def initialize_mongodb(self) -> None:
        """
        Initialize MongoDB connection with error handling.

        Establishes connection to MongoDB using environment variables
        and sets up the database and collection references.

        Raises:
            APIException: If MongoDB connection fails
        """
        try:
            connection_string = os.getenv("MONGO_CONNECTION_STRING")
            if not connection_string:
                raise ValueError("MongoDB connection string not found in environment")

            logger.info("Initializing MongoDB connection")
            self.client = MongoClient(connection_string)
            self.db = self.client["WTP"]
            self.collection = self.db["whbriefingroom"]
            # Test connection
            self.db.command("ping")
            logger.info("Successfully connected to MongoDB")
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB: {e}")
            raise APIException("Failed to connect to document database")

    def get_document_details(self, object_ids: List[ObjectId]) -> List[Dict[str,Any]]:
        """
        Fetch document details from MongoDB.

        Args:
            object_ids (list): List of MongoDB ObjectIds to retrieve

        Returns:
            list: List of document details including metadata
        """
        try:
            return list(
                self.collection.find({"_id": {"$in": object_ids}})
            )
        except Exception as e:
            logger.error(f"Error fetching document details: {e}")
            return []

    def get_random_documents(self, size: int = 6) -> List[Dict[str, Any]]:
        """
        Get random documents when no query is provided.

        Args:
            size (int): Number of random documents to retrieve

        Returns:
            list: List of random documents
        """
        try:
            return list(self.collection.aggregate([{"$sample": {"size": size}}]))
        except Exception as e:
            logger.error(f"Error fetching random documents: {e}")
            return []

    def format_results(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format documents for response.

        Transforms MongoDB documents into a consistent format with
        proper ID handling and metadata organization.

        Args:
            documents (list): Raw documents from MongoDB

        Returns:
            list: Formatted document list for API response
        """
        return [
            {
                "id": str(doc["_id"]),
                "title": doc.get("title", "Untitled"),
                "summary": doc.get("summary", "No summary available"),
                "url": doc.get("url", "#"),
                "date_posted": doc.get("date_posted"),
                "category": doc.get("category", "Uncategorized"),
            }
            for doc in documents
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Handle GET requests for document search.

        Supports two modes:
        1. Query-based search using RAG system
        2. Random document retrieval when no query provided

        Args:
            request: HTTP request with optional 'query' parameter

        Returns:
            Response: List of documents matching the query or random documents
        """
        try:
            query = request.query_params.get("query", "")
            logger.info(f"Processing search request. Query: '{query}'")

            if query:
                # RAG system search
                try:
                    rag_system = RAGSystem()
                    doc_ids = rag_system.handle_search_query(query)
                    logger.info(f"RAG system returned {len(doc_ids)} document IDs")

                    # Convert to ObjectIds
                    object_ids = [
                        ObjectId(id_str)
                        for id_str in doc_ids
                        if ObjectId.is_valid(id_str)
                    ]
                    if not object_ids:
                        logger.warning("No valid document IDs found")
                        return Response({"query": query, "results": []})

                    # Get and sort documents
                    documents = self.get_document_details(object_ids)
                    id_to_doc = {str(doc["_id"]): doc for doc in documents}
                    documents = [
                        id_to_doc[id_str] for id_str in doc_ids if id_str in id_to_doc
                    ]

                except ValidationError as e:
                    return self.handle_validation_error(e, "processing search query")

            else:
                # Random documents
                documents = self.get_random_documents()

            results = self.format_results(documents)
            logger.info(f"Returning {len(results)} results")

            return Response({"query": query, "results": results, "total": len(results)})

        except pymongo.errors.PyMongoError as e:
            return self.handle_database_error(e, "searching documents")
        except Exception as e:
            self.handle_unexpected_error(e, "processing search request")
