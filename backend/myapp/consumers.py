"""
WebSocket consumer for handling real-time chat communication.

This module implements the WebSocket consumer that handles:
- Real-time chat message processing
- Authentication and session validation
- Message streaming using the RAG system
- Chat history persistence
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError
from .rag_system import RAGSystem
from asgiref.sync import sync_to_async
import asyncio

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling chat messages.

    Handles WebSocket lifecycle (connect, receive, disconnect) and manages
    chat message processing with the RAG system. Includes authentication,
    session validation, and error handling.

    Attributes:
        user: The authenticated user for this connection
        session_id: UUID of the chat session
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = None

    async def connect(self) -> None:
        """
        Handles WebSocket connection requests.

        Validates user authentication and session ownership before accepting
        the connection. Closes connection with appropriate error codes if
        validation fails.

        Error Codes:
            4001: Unauthenticated user
            4004: Invalid session access
            4000: General connection error
        """
        try:
            # Authentication check
            if not self.scope["user"].is_authenticated:
                logger.warning("Rejected unauthenticated WebSocket connection attempt")
                await self.close(code=4003)
                return

            self.user = self.scope["user"]
            self.session_id = self.scope["url_route"]["kwargs"].get("session_id")
            if not self.session_id:
                await self.close(code=4000)
                return

            logging.info(
                f"WebSocket connection attempt: session={self.session_id}, user={self.user}"
            )

            # Validate session ownership
            from .models import ChatSession

            try:
                await sync_to_async(ChatSession.objects.get)(
                    session_id=self.session_id, user=self.user
                )
            except ObjectDoesNotExist:
                logger.warning(f"Invalid session access attempt: {self.session_id}")
                await self.close(code=4004)
                return

            logger.info(f"WebSocket connected: session={self.session_id}")
            await self.accept()

        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            await self.close(code=4000)

    async def disconnect(self, close_code: int) -> None:
        """
        Handles WebSocket disconnection.

        Args:
            close_code: The code indicating why the connection was closed
        """
        logger.info(
            f"WebSocket disconnected: session={self.session_id}, code={close_code}"
        )

    async def send_error(self, message, code=None) -> None:
        """
        Sends an error message to the client.

        Args:
            message (str): Human-readable error message
            code (str, optional): Error code for client-side handling
        """
        await self.send(
            text_data=json.dumps({"type": "error", "message": message, "code": code})
        )

    async def receive(self, text_data) -> None:
        """
        Processes incoming WebSocket messages.

        Handles the complete lifecycle of a chat message:
        1. Message parsing and validation
        2. Session retrieval and validation
        3. RAG system processing with streaming response
        4. Message persistence in database

        Error Codes:
            INVALID_FORMAT: Message parsing failed
            SESSION_NOT_FOUND: Chat session not found
            DATABASE_ERROR: Database operation failed
            SAVE_ERROR: Failed to save chat messages
            SYSTEM_ERROR: Unexpected system error

        Args:
            text_data (str): JSON string containing the message
        """
        try:
            # Parse message
            try:
                data = json.loads(text_data)
                query = data["message"]
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Invalid message format: {str(e)}")
                await self.send_error("Invalid message format", "INVALID_FORMAT")
                return

            logger.info(f"Processing message: session={self.session_id}")

            # Get chat session
            try:
                from .models import ChatSession, ChatMessage

                chat_session = await sync_to_async(ChatSession.objects.get)(
                    session_id=self.session_id, user=self.user
                )
            except ObjectDoesNotExist:
                logger.error(f"Chat session not found: {self.session_id}")
                await self.send_error("Chat session not found", "SESSION_NOT_FOUND")
                return
            except DatabaseError as e:
                logger.error(f"Database error: {str(e)}")
                await self.send_error("Database error occurred", "DATABASE_ERROR")
                return

            # Process with RAG system
            try:
                rag_system = RAGSystem()
                full_response = ""
                async for chunk in rag_system.handle_chat_query(query):
                    full_response += chunk
                    await self.send(
                        json.dumps(
                            {
                                "type": "chunk",
                                "chunk": chunk,
                            }
                        )
                    )
                # Success response
                await self.send(
                    text_data=json.dumps(
                        {"type": "complete", "message": "Streaming finished"}
                    )
                )
                logger.info(f"Message finished successfully: session={self.session_id}")

                # Save messages
                try:
                    await sync_to_async(ChatMessage.objects.create)(
                        session=chat_session, role="human", content=query
                    )
                    await sync_to_async(ChatMessage.objects.create)(
                        session=chat_session, role="ai", content=full_response
                    )
                    logger.info(
                        f"Message processed successfully: session={self.session_id}"
                    )

                except DatabaseError as e:
                    logger.error(f"Failed to save chat messages: {str(e)}")
                    await self.send_error("Failed to save messages", "SAVE_ERROR")
                    return

            except asyncio.CancelledError:
                logger.info(f"Client cancelled request: session={self.session_id}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error in RAG system: {str(e)}")
                await self.send_error("An unexpected error occurred", "SYSTEM_ERROR")

        except Exception as e:
            logger.error(f"Unexpected error in receive: {str(e)}")
            await self.send_error("An unexpected error occurred", "SYSTEM_ERROR")
