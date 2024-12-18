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
    async def connect(self):
        try:
            # Authentication check
            if not self.scope["user"].is_authenticated:
                logger.warning("Rejected unauthenticated WebSocket connection attempt")
                await self.close(code=4001)
                return

            self.user = self.scope["user"]
            self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
            logging.info(f"WebSocket connection attempt: session={self.session_id}, user={self.user}")
            
            # Validate session ownership
            from .models import ChatSession
            try:
                await sync_to_async(ChatSession.objects.get)(
                    session_id=self.session_id,
                    user=self.user
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

    async def disconnect(self, close_code):
        logger.info(f"WebSocket disconnected: session={self.session_id}, code={close_code}")

    async def send_error(self, message, code=None):
        """Helper method to send error messages"""
        await self.send(text_data=json.dumps({
            "type": "error",
            "message": message,
            "code": code
        }))

    async def receive(self, text_data):
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
                    session_id=self.session_id,
                    user=self.user
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
                    await self.send(json.dumps({
                        "type": "chunk",
                        "chunk": chunk,
                    }))
                # Success response
                await self.send(text_data=json.dumps({
                    "type": "complete",
                    "message": "Streaming finished"
                }))
                logger.info(f"Message finished successfully: session={self.session_id}")


                # Save messages
                try:
                    await sync_to_async(ChatMessage.objects.create)(
                        session=chat_session,
                        role="human",
                        content=query
                    )
                    await sync_to_async(ChatMessage.objects.create)(
                        session=chat_session,
                        role="ai",
                        content=full_response
                    )
                    logger.info(f"Message processed successfully: session={self.session_id}")

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
