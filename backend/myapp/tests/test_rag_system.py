import unittest
from unittest.mock import Mock, patch
import asyncio
from ..rag_system import RAGSystem
from langchain_community.chat_message_histories import ChatMessageHistory


class TestRAGSystem(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.rag_system = RAGSystem()
        self.test_question = "What is some information on immigration?"

    # Test RAG system initialization
    @patch("myapp.rag_system.RAGSystem._load_environment_variables")
    def test_initialization(self, mock_load_env):
        rag_system = RAGSystem()
        self.assertIsNotNone(rag_system.llm)
        self.assertIsNotNone(rag_system.embeddings)
        self.assertIsNotNone(rag_system.vector_store)
        self.assertIsNotNone(rag_system.generator)
        self.assertIsNotNone(rag_system.search)

    # Test chat query handling
    @patch("myapp.rag_system.Generator.invoke_async")
    async def test_handle_chat_query(self, mock_invoke):
        # Mock the async generator response
        async def mock_response():
            yield "Test response"

        mock_invoke.return_value = mock_response()

        # Test chat query
        response = self.rag_system.handle_chat_query(self.test_question)
        result = await response.__anext__()  # Get first response using __anext__()

        # Verify the generator was called
        mock_invoke.assert_called_once_with(self.test_question)
        self.assertEqual(result, "Test response")

    # Test search query handling
    @patch("myapp.rag_system.Search.invoke")
    def test_handle_search_query(self, mock_search):
        # Mock search response
        mock_search.return_value = [
            {"content": "Test document", "metadata": {"source": "test.pdf"}}
        ]

        # Test search query
        results = self.rag_system.handle_search_query(self.test_question)

        # Verify search was called and returned results
        mock_search.assert_called_once_with(self.test_question)
        self.assertTrue(len(results) > 0)

    # Test chat history management
    def test_load_memory(self):
        # Create test chat history
        chat_history = ChatMessageHistory()
        chat_history.add_user_message("Test user message")
        chat_history.add_ai_message("Test AI response")

        # Load chat history
        self.rag_system.load_memory(chat_history)

        # Verify chat history was loaded
        self.assertEqual(
            self.rag_system.generator.chat_history.messages, chat_history.messages
        )


if __name__ == "__main__":
    unittest.main()
