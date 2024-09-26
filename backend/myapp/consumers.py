import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .rag_system import RAGSystem
from asgiref.sync import sync_to_async
import asyncio

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        print(f"WebSocket connection request for session ID: {self.session_id}")
        await self.accept()

    async def disconnect(self, close_code):
        print(f"WebSocket disconnected for session ID: {self.session_id}")

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        query = text_data_json['message']
        session_id = text_data_json.get('session_id')
        from .models import ChatSession, ChatMessage
        
        user = self.scope["user"]
        
        if session_id:
            chat_session = await sync_to_async(ChatSession.objects.get)(session_id=session_id, user=user)
        else:
            chat_session = await sync_to_async(ChatSession.objects.create)(user=user)
        
        rag_system = RAGSystem()
        
        # Initial message --> prob not necessary anymore
        await self.send(json.dumps({
            'type': 'initial',
            'session_id': str(chat_session.session_id),
            'is_streaming': True,
        }))
        
        full_response = ""
        async for chunk in rag_system.handle_query(query):
            full_response += chunk
            await self.send(json.dumps({
                'type': 'chunk',
                'chunk': chunk,
            }))
        print(f"Finished streaming this response: {full_response}")
        
        # Handle chatmessage save
        await sync_to_async(ChatMessage.objects.create)(session=chat_session, role='human', content=query)
        await sync_to_async(ChatMessage.objects.create)(session=chat_session, role='ai', content=full_response)

        # Final message
        await self.send(text_data=json.dumps({
            'status': 'complete',
            'message': 'Streaming finished'
        }))
    """
    
    

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        session_id = text_data_json.get('session_id')
        from .models import ChatSession, ChatMessage


        user = self.scope["user"]
        
        if session_id:
            chat_session = await sync_to_async(ChatSession.objects.get)(session_id=session_id, user=user)
        else:
            chat_session = await sync_to_async(ChatSession.objects.create)(user=user)

        rag_system = RAGSystem()
        
        await self.send(json.dumps({
            'type': 'initial',
            'session_id': str(chat_session.session_id),
            'is_streaming': True,
        }))


        full_response = ""
        for chunk in rag_system.handle_query(message):
            full_response += chunk
            await self.send(json.dumps({
                'type': 'chunk',
                'chunk': chunk,
            }))

        await sync_to_async(ChatMessage.objects.create)(session=chat_session, role='human', content=message)
        await sync_to_async(ChatMessage.objects.create)(session=chat_session, role='ai', content=full_response)

        await self.send(json.dumps({
            'type': 'final',
            'response': full_response,
            'is_streaming': False,
        }))
        """