# Ignore cryptography deprecation warnings for viewing in terminal
import warnings
from cryptography.utils import CryptographyDeprecationWarning

warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from ..models import ChatSession


class TestViews(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create test user
        self.user_data = {"username": "testuser", "password": "testpassword"}
        self.user = User.objects.create_user(**self.user_data)

        # Get auth token
        response = self.client.post("/api-token-auth/", self.user_data)
        self.token = response.data["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token}")

    # Test user registration
    def test_user_creation(self):
        new_user_data = {"username": "newuser", "password": "newpassword"}
        response = self.client.post("/api/users/", new_user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    # Test chat session creation, update, and deletion
    def test_chat_session_lifecycle(self):
        # Create chat session
        response = self.client.post("/api/chat/new/", {"message": "Hello"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        session_id = response.data["session_id"]

        # Update chat session
        update_data = {"name": "Updated Chat"}
        response = self.client.patch(f"/api/chat/sessions/{session_id}/", update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Chat")

        # Delete chat session
        response = self.client.delete(f"/api/chat/sessions/{session_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ChatSession.objects.filter(id=session_id).exists())

    # Test document search functionality
    def test_document_search(self):
        # Test with query
        response = self.client.get("/api/search/", {"query": "test policy"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

        # Test random documents (no query)
        response = self.client.get("/api/search/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

    # Test user settings management
    def test_user_settings(self):
        # Get settings
        response = self.client.get("/api/user_settings/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Update settings
        settings_data = {"first_name": "John", "last_name": "Smith"}
        response = self.client.post("/api/user_settings/", settings_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["status"], "settings updated")
        self.assertEqual(response.data["updated_fields"]["first_name"], "John")
        self.assertEqual(response.data["updated_fields"]["last_name"], "Smith")

    # Test error handling for various scenarios
    def test_error_handling(self):
        # Test unauthorized access
        self.client.credentials()  # Remove auth
        response = self.client.get("/api/chat/sessions/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test invalid session access
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token}")
        response = self.client.get("/api/chat/sessions/999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
