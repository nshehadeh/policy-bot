import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .rag_system import RAGSystem
from asgiref.sync import sync_to_async
import asyncio

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Ensure the user is authenticated
        if self.scope["user"].is_authenticated:
            self.user = self.scope["user"]  # Get the logged-in user
        else:
            await self.close()  # Reject connection if user isn't authenticated

        self.session_id = self.scope['url_route']['kwargs']['session_id']
        print(f"WebSocket connection request for session ID: {self.session_id} & user {self.user}")
        await self.accept()

    async def disconnect(self, close_code):
        print(f"WebSocket disconnected for session ID: {self.session_id}")

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        query = text_data_json['message']
        print("Received message on session: " + str(self.session_id) + " \n which should match: " + str(self.session_id))
        from .models import ChatSession, ChatMessage
        
        chat_session = await sync_to_async(ChatSession.objects.get)(session_id=self.session_id, user=self.user)
        rag_system = RAGSystem()
        
        full_response = ""
        async for chunk in rag_system.handle_chat_query(query):
            full_response += chunk
            await self.send(json.dumps({
                'type': 'chunk',
                'chunk': chunk,
            }))

        # Final message
        await self.send(text_data=json.dumps({
            'status': 'complete',
            'message': 'Streaming finished'
        }))
        # After sending the full response via WebSocket
        await sync_to_async(ChatMessage.objects.create)(session=chat_session, role='human', content=query)
        await sync_to_async(ChatMessage.objects.create)(session=chat_session, role='ai', content=full_response)