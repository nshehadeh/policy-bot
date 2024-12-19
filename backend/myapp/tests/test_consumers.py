# TODO IN PROGRESS TESTING

from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase
from django.contrib.auth.models import User
from django.urls import re_path
from channels.routing import URLRouter
from channels.db import database_sync_to_async
from ..consumers import ChatConsumer
from ..models import ChatSession

class TestChatConsumer(TransactionTestCase):
    async def asyncSetUp(self):
        # Create test user
        self.user = await database_sync_to_async(User.objects.create_user)(
            username='testuser',
            password='testpass'
        )
        
        # Create test chat session
        self.session = await database_sync_to_async(ChatSession.objects.create)(
            user=self.user
        )
        self.session_id = str(self.session.session_id)
        
        # Set up application with URL routing
        self.application = URLRouter([
            re_path(r"ws/chat/(?P<session_id>[^/]+)/$", ChatConsumer.as_asgi()),
        ])
    
    async def test_websocket_connect(self):
        await self.asyncSetUp()
        # Create communicator
        communicator = WebsocketCommunicator(
            self.application,
            f"/ws/chat/{self.session_id}/"
        )
        communicator.scope["user"] = self.user
        
        try:
            # Connect and check it succeeds
            connected, _ = await communicator.connect()
            self.assertTrue(connected)
            
            # Verify no messages waiting
            await communicator.receive_nothing()
        finally:
            await communicator.disconnect()
            
    # TODO In progress
    async def test_websocket_send_message(self):
        await self.asyncSetUp()
        # Create communicator
        communicator = WebsocketCommunicator(
            self.application,
            f"/ws/chat/{self.session_id}/"
        )
        communicator.scope["user"] = self.user
        
        try:
            # Connect
            connected, _ = await communicator.connect()
            self.assertTrue(connected)
            
            # Send message
            await communicator.send_json_to({"message": "Hello"})
            
            # Check response
            response = await communicator.receive_json_from()
            self.assertIn('type', response)
        finally:
            await communicator.disconnect()
    
    # TODO In progress        
    async def test_unauthenticated_connection(self):
        await self.asyncSetUp()
        # Create communicator without auth
        communicator = WebsocketCommunicator(
            self.application,
            f"/ws/chat/{self.session_id}/"
        )
        
        try:
            # Try to connect (fail)
            connected, close_code = await communicator.connect()
            self.assertFalse(connected)
            self.assertEqual(close_code, 4003)  # Authentication failed
        finally:
            await communicator.disconnect()
