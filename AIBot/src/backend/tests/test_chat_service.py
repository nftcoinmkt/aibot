"""
Comprehensive tests for AI chat service functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.backend.ai_service.chat_service import chat_service
from src.backend.ai_service import schemas


class TestChatService:
    """Test chat service functionality."""

    @patch('src.backend.ai_service.ai_providers.GeminiProvider.generate_response')
    def test_process_chat_message_gemini(self, mock_gemini, create_test_user):
        """Test chat message processing with Gemini."""
        mock_gemini.return_value = "Hello! How can I help you today?"
        
        response, provider = chat_service.process_chat_message(
            create_test_user.id, 
            create_test_user.tenant_name, 
            "Hello, AI!"
        )
        
        assert response == "Hello! How can I help you today?"
        assert provider == "gemini"
        mock_gemini.assert_called_once_with("Hello, AI!")

    @patch('src.backend.ai_service.ai_providers.GroqProvider.generate_response')
    @patch('src.backend.core.settings.settings.AI_PROVIDER', 'groq')
    def test_process_chat_message_groq(self, mock_groq, create_test_user):
        """Test chat message processing with Groq."""
        mock_groq.return_value = "Hi there! I'm here to assist you."
        
        response, provider = chat_service.process_chat_message(
            create_test_user.id, 
            create_test_user.tenant_name, 
            "Hello, AI!"
        )
        
        assert response == "Hi there! I'm here to assist you."
        assert provider == "groq"
        mock_groq.assert_called_once_with("Hello, AI!")

    @patch('src.backend.ai_service.ai_providers.GeminiProvider.generate_response')
    def test_process_chat_message_with_error(self, mock_gemini, create_test_user):
        """Test chat message processing with AI provider error."""
        mock_gemini.side_effect = Exception("API Error")
        
        response, provider = chat_service.process_chat_message(
            create_test_user.id, 
            create_test_user.tenant_name, 
            "Hello, AI!"
        )
        
        assert "trouble processing" in response
        assert "Error: API Error" in response
        assert provider == "gemini"

    def test_save_chat_message(self, create_test_user):
        """Test saving chat message to tenant database."""
        message = "Test message"
        response = "Test response"
        provider = "gemini"
        
        chat_message = chat_service.save_chat_message(
            create_test_user.tenant_name,
            create_test_user.id,
            message,
            response,
            provider
        )
        
        assert chat_message.user_id == create_test_user.id
        assert chat_message.message == message
        assert chat_message.response == response
        assert chat_message.provider == provider

    def test_get_chat_history(self, create_test_user):
        """Test retrieving chat history."""
        # First, create some chat messages
        for i in range(3):
            chat_service.save_chat_message(
                create_test_user.tenant_name,
                create_test_user.id,
                f"Message {i}",
                f"Response {i}",
                "gemini"
            )
        
        history = chat_service.get_chat_history(
            create_test_user.tenant_name,
            create_test_user.id,
            skip=0,
            limit=10
        )
        
        assert len(history) == 3
        # Should be in reverse chronological order
        assert history[0].message == "Message 2"

    def test_get_chat_statistics(self, create_test_user):
        """Test getting chat statistics."""
        # Create some chat messages with different providers
        chat_service.save_chat_message(
            create_test_user.tenant_name,
            create_test_user.id,
            "Gemini message 1",
            "Gemini response 1",
            "gemini"
        )
        chat_service.save_chat_message(
            create_test_user.tenant_name,
            create_test_user.id,
            "Gemini message 2",
            "Gemini response 2",
            "gemini"
        )
        chat_service.save_chat_message(
            create_test_user.tenant_name,
            create_test_user.id,
            "Groq message 1",
            "Groq response 1",
            "groq"
        )
        
        stats = chat_service.get_chat_statistics(create_test_user.tenant_name)
        
        assert stats["total_messages"] == 3
        assert stats["unique_users"] == 1
        assert stats["messages_by_provider"]["gemini"] == 2
        assert stats["messages_by_provider"]["groq"] == 1


class TestChatEndpoints:
    """Test chat API endpoints."""

    @patch('src.backend.ai_service.chat_service.chat_service.process_chat_message')
    def test_chat_endpoint_success(self, mock_process, client: TestClient, auth_headers):
        """Test successful chat API call."""
        mock_process.return_value = ("Hello! How can I help?", "gemini")
        
        chat_data = {"message": "Hello, AI!"}
        response = client.post("/api/v1/chat", json=chat_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Hello! How can I help?"
        assert data["provider"] == "gemini"

    def test_chat_endpoint_unauthenticated(self, client: TestClient):
        """Test chat endpoint without authentication."""
        chat_data = {"message": "Hello, AI!"}
        response = client.post("/api/v1/chat", json=chat_data)
        
        assert response.status_code == 401

    def test_chat_endpoint_empty_message(self, client: TestClient, auth_headers):
        """Test chat endpoint with empty message."""
        chat_data = {"message": ""}
        response = client.post("/api/v1/chat", json=chat_data, headers=auth_headers)
        
        # Should still work but might return a default response
        assert response.status_code == 200

    @patch('src.backend.ai_service.chat_service.chat_service.get_chat_history')
    def test_chat_history_endpoint(self, mock_history, client: TestClient, auth_headers):
        """Test chat history endpoint."""
        mock_history.return_value = [
            MagicMock(
                id=1,
                message="Test message",
                response="Test response",
                provider="gemini",
                created_at="2023-01-01T00:00:00"
            )
        ]
        
        response = client.get("/api/v1/chat/history", headers=auth_headers)
        
        assert response.status_code == 200
        # Note: The actual response format depends on the schema serialization

    def test_chat_history_endpoint_unauthenticated(self, client: TestClient):
        """Test chat history endpoint without authentication."""
        response = client.get("/api/v1/chat/history")
        
        assert response.status_code == 401

    def test_chat_history_pagination(self, client: TestClient, auth_headers):
        """Test chat history endpoint with pagination."""
        response = client.get("/api/v1/chat/history?skip=0&limit=5", headers=auth_headers)
        
        assert response.status_code == 200

    @patch('src.backend.ai_service.chat_service.chat_service.get_chat_statistics')
    def test_chat_stats_endpoint(self, mock_stats, client: TestClient, auth_headers):
        """Test chat statistics endpoint."""
        mock_stats.return_value = {
            "total_messages": 10,
            "unique_users": 2,
            "messages_by_provider": {"gemini": 6, "groq": 4}
        }
        
        response = client.get("/api/v1/chat/stats", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_messages"] == 10
        assert data["unique_users"] == 2


class TestAIProviders:
    """Test AI provider implementations."""

    @patch('groq.Groq')
    def test_groq_provider(self, mock_groq_client):
        """Test Groq provider functionality."""
        from src.backend.ai_service.ai_providers import GroqProvider
        
        # Mock the Groq client response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Groq response"
        mock_groq_client.return_value.chat.completions.create.return_value = mock_response
        
        provider = GroqProvider()
        response = provider.generate_response("Test message")
        
        assert response == "Groq response"

    @patch('google.generativeai.GenerativeModel')
    def test_gemini_provider(self, mock_gemini_model):
        """Test Gemini provider functionality."""
        from src.backend.ai_service.ai_providers import GeminiProvider
        
        # Mock the Gemini model response
        mock_response = MagicMock()
        mock_response.text = "Gemini response"
        mock_gemini_model.return_value.generate_content.return_value = mock_response
        
        provider = GeminiProvider()
        response = provider.generate_response("Test message")
        
        assert response == "Gemini response"

    def test_provider_error_handling(self):
        """Test AI provider error handling."""
        from src.backend.ai_service.ai_providers import GroqProvider
        
        # Test with no API key configured
        provider = GroqProvider()
        provider.client = None
        
        with pytest.raises(ValueError, match="Groq API key not configured"):
            provider.generate_response("Test message")
