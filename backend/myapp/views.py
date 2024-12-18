from django.shortcuts import render
from django.contrib.auth import get_user_model
from pymongo.database import Database
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import APIException, ValidationError
from rest_framework import status
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
from langchain_community.chat_message_histories import ChatMessageHistory
from django.shortcuts import get_object_or_404
import json
from pymongo import MongoClient
from django.conf import settings
import os
from bson import ObjectId
from django.db import DatabaseError
import logging

logger = logging.getLogger(__name__)


class BaseAPIView(APIView):
    """
    Base API view with common error handling.
    All views should inherit from this class to get consistent error handling.
    """

    def handle_database_error(self, e: DatabaseError, operation: str) -> Response:
        logger.error(f"Database error in {operation}: {e}")
        return Response(
            {"error": f"Database error while {operation}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    def handle_validation_error(self, e: ValidationError, operation: str) -> Response:
        logger.warning(f"Validation error in {operation}: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def handle_unexpected_error(self, e: Exception, operation: str) -> None:
        logger.error(f"Unexpected error in {operation}: {e}")
        raise APIException(f"Unexpected error while {operation}")


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


class ChatView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
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

    permission_classes = [IsAuthenticated]

    # Helper method for getting chat session
    def get_chat_session(self, session_id):
        return get_object_or_404(
            ChatSession, session_id=session_id, user=self.request.user
        )

    # Update chat name
    def patch(self, request, session_id, *args, **kwargs):
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

    # Delete chat
    def delete(self, request, session_id, *args, **kwargs):
        """Delete chat session"""
        try:
            session = self.get_chat_session(session_id)
            session.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DatabaseError as e:
            return self.handle_database_error(e, "deleting chat session")
        except Exception as e:
            self.handle_unexpected_error(e, "deleting chat session")


class LoadPreviousChatView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
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

    def post(self, request, *args, **kwargs):
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
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
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

    def post(self, request, *args, **kwargs):
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
    View for searching documents stored in MongoDB using RAG system.
    Returns most recent documents if no query is provided,
    or most relevant documents based on similarity search if query exists.
    """

    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = None
        self.db = None
        self.collection = None
        self.initialize_mongodb()

    def initialize_mongodb(self):
        """Initialize MongoDB connection with error handling"""
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
            logger.error(f"Failed to initialize MongoDB: {str(e)}")
            raise

    def get_document_details(self, object_ids):
        """Fetch document details from MongoDB"""
        try:
            documents = list(
                self.collection.find(
                    {"_id": {"$in": object_ids}},
                    {
                        "_id": 1,
                        "title": 1,
                        "summary": 1,
                        "url": 1,
                        "date_posted": 1,
                        "category": 1,
                    },
                )
            )
            logger.info(f"Retrieved {len(documents)} documents from MongoDB")
            return documents
        except Exception as e:
            logger.error(f"Error fetching documents from MongoDB: {str(e)}")
            raise

    def get_random_documents(self, size=6):
        """Get random documents when no query is provided"""
        try:
            return list(
                self.collection.aggregate(
                    [
                        {"$match": {"summary": {"$exists": True}}},
                        {"$sample": {"size": size}},
                        {
                            "$project": {
                                "_id": 1,
                                "title": 1,
                                "summary": 1,
                                "url": 1,
                                "date_posted": 1,
                                "category": 1,
                            }
                        },
                    ]
                )
            )
        except Exception as e:
            logger.error(f"Error fetching random documents: {str(e)}")
            raise

    def format_results(self, documents):
        """Format documents for response"""
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

    def get(self, request, *args, **kwargs):
        """Handle GET requests for document search"""
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
