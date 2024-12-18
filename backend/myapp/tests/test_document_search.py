from django.test import TestCase
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock
from bson import ObjectId
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token


class TestDocumentSearchView(TestCase):
    def setUp(self):
        # Create a test user and authenticate
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.url = "/api/search/"

    @patch("myapp.views.RAGSystem")
    @patch("myapp.views.MongoClient")
    def test_document_search_no_query(self, mock_mongo_client, mock_rag_system):
        """
        Test DocumentSearchView with no query.
        Should return random documents from MongoDB.
        """
        # Mock MongoDB response
        mock_collection = MagicMock()
        mock_collection.aggregate.return_value = [
            {
                "_id": ObjectId("507f1f77bcf86cd799439011"),
                "title": "Document 1",
                "summary": "Summary 1",
                "url": "http://example.com/1",
                "date_posted": "2024-01-01",
                "category": "Policy"
            },
            {
                "_id": ObjectId("507f1f77bcf86cd799439012"),
                "title": "Document 2",
                "summary": "Summary 2",
                "url": "http://example.com/2",
                "date_posted": "2024-01-02",
                "category": "News"
            }
        ]
        mock_mongo_client.return_value.__getitem__.return_value.__getitem__.return_value = mock_collection

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["results"]), 2)
        self.assertEqual(data["query"], "")
        self.assertEqual(data["results"][0]["title"], "Document 1")
        self.assertEqual(data["results"][1]["category"], "News")

    @patch("myapp.views.RAGSystem")
    @patch("myapp.views.MongoClient")
    def test_document_search_with_query(self, mock_mongo_client, mock_rag_system):
        """
        Test DocumentSearchView with a query.
        Should return relevant documents based on RAG system search.
        """
        # Mock RAG system response
        mock_rag_system.return_value.search.return_value = [
            "507f1f77bcf86cd799439011"
        ]

        # Mock MongoDB response
        mock_collection = MagicMock()
        mock_collection.find.return_value = [
            {
                "_id": ObjectId("507f1f77bcf86cd799439011"),
                "title": "Relevant Document",
                "summary": "Content matching query",
                "url": "http://example.com/relevant",
                "date_posted": "2024-01-03",
                "category": "Policy"
            }
        ]
        mock_mongo_client.return_value.__getitem__.return_value.__getitem__.return_value = mock_collection

        response = self.client.get(self.url, {"query": "test query"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["query"], "test query")
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["title"], "Relevant Document")
        self.assertEqual(data["results"][0]["category"], "Policy")

    @patch("myapp.views.RAGSystem")
    def test_document_search_invalid_query(self, mock_rag_system):
        """
        Test DocumentSearchView with an invalid query that causes RAG system error.
        """
        # Mock RAG system to raise an error
        mock_rag_system.return_value.search.side_effect = ValueError("Invalid query format")
        
        response = self.client.get(self.url, {"query": "invalid!@#$"})
        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.json())
        self.assertEqual(response.json()["error"], "Invalid query format")

    @patch("myapp.views.RAGSystem")
    @patch("myapp.views.MongoClient")
    def test_document_search_mongodb_error(self, mock_mongo_client, mock_rag_system):
        """
        Test DocumentSearchView when MongoDB connection fails.
        """
        # Mock MongoDB to raise an error
        mock_mongo_client.side_effect = Exception("MongoDB connection failed")
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.json())
        self.assertEqual(response.json()["error"], "MongoDB connection failed")
