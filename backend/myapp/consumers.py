import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .rag_system import RAGSystem
from asgiref.sync import sync_to_async
import asyncio

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'chat_{self.session_id}'

        print(f"WebSocket connection request for session ID: {self.session_id}")

        # Accept WebSocket connection
        await self.accept()

        # Simulate streaming data over WebSocket
        await self.fake_stream_data()

    async def disconnect(self, close_code):
        print(f"WebSocket disconnected for session ID: {self.session_id}")

    async def fake_stream_data(self):
        # Simulate sending 5 chunks of data over time
        for i in range(5):
            chunk = f"Data chunk {i + 1}"
            print(f"Sending chunk: {chunk}")

            # Send the chunk to the WebSocket
            await self.send(text_data=json.dumps({
                'chunk': chunk
            }))

            # Simulate a delay (1 second) between chunks to mimic streaming
            await asyncio.sleep(1)

        # Signal end of streaming
        await self.send(text_data=json.dumps({
            'status': 'complete',
            'message': 'Streaming finished'
        }))
        print("Finished streaming data") 
   
    """
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'chat_{self.session_id}'

        # Print the session ID and the WebSocket path
        print(f"WebSocket connection request for session ID: {self.session_id}")

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        print(f"WebSocket disconnected for session ID: {self.session_id}")
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

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