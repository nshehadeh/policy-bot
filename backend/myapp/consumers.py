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
from asgiref.sync import sync_to_async
import asyncio
from rag.chat_graph import ChatGraph
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage

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
        chat_graph: ChatGraph instance for this session
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = None
        self.chat_graph = None

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
            from .models import ChatSession, ChatMessage

            try:
                self.chat_session = await sync_to_async(ChatSession.objects.get)(
                    session_id=self.session_id, user=self.user
                )
                
                # Load existing chat history
                chat_messages = await sync_to_async(list)(
                    ChatMessage.objects.filter(session=self.chat_session).order_by("created_at")
                )
                
                # Create chat history for the graph
                history = ChatMessageHistory()
                for message in chat_messages:
                    if message.role == "human":
                        history.add_user_message(message.content)
                    elif message.role == "ai":
                        history.add_ai_message(message.content)
                
                logger.info(f"Loaded {len(chat_messages)} messages for session {self.session_id}")
                
                # Initialize chat graph with loaded history
                self.chat_graph = ChatGraph(chat_history=history)
                logger.info(f"Initialized ChatGraph with {len(history.messages)} message history, for session {self.session_id}")
                
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
        try:
            if self.chat_graph:
                # Get new chats from the graph
                new_chats = self.chat_graph.get_new_chats()
                logger.info(f"Retrieved {len(new_chats)} new chats for session={self.session_id}")
                
                # Save new chats to database
                from .models import ChatMessage
                
                saved_count = 0
                for chat in new_chats:
                    #TODO Extract metadata if it exists
                                        
                    await sync_to_async(ChatMessage.objects.create)(
                        session=self.chat_session,
                        content=chat.content,
                        role="human" if isinstance(chat, HumanMessage) else "ai",
                    )
                    saved_count += 1
                    
                logger.info(
                    f"Successfully saved {saved_count} messages for session={self.session_id}"
                )
            
            logger.info(
                f"WebSocket disconnected: session={self.session_id}, code={close_code}"
            )
        except Exception as e:
            logger.error(f"Error saving chat history: {str(e)}")

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
        2. ChatGraph processing with streaming response
        3. Message streaming to client

        Error Codes:
            INVALID_FORMAT: Message parsing failed
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

            if not self.chat_graph:
                logger.error("ChatGraph not initialized")
                await self.send_error("System error occurred", "SYSTEM_ERROR")
                return

            # Process with ChatGraph
            try:
                logger.info(f"Starting ChatGraph processing for query: session={self.session_id}")
                async for message in self.chat_graph.process_query_async(query):
                    await self.send(json.dumps(message))

                # Success response
                await self.send(
                    text_data=json.dumps(
                        {"type": "complete", "message": "Streaming finished"}
                    )
                )
                logger.info(f"Message finished successfully: session={self.session_id}")


            except Exception as e:
                logger.error(f"Chat processing error: {str(e)}")
                await self.send_error("Failed to process chat", "SYSTEM_ERROR")
                return

        except Exception as e:
            logger.error(f"Unexpected error in receive: {str(e)}")
            await self.send_error("System error occurred", "SYSTEM_ERROR")
