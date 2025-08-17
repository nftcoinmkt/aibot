import os
from abc import ABC, abstractmethod
from groq import Groq
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_not_exception_type

from src.backend.core.settings import settings


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    def generate_response(self, message: str) -> str:
        """Generate response from AI provider."""
        pass


class GroqProvider(AIProvider):
    """Groq AI provider implementation."""
    
    def __init__(self):
        if settings.GROQ_API_KEY:
            os.environ["GROQ_API_KEY"] = settings.GROQ_API_KEY
            self.client = Groq()
        else:
            self.client = None

    @retry(
        retry=retry_if_not_exception_type(ValueError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    def generate_response(self, message: str) -> str:
        """Generate response using Groq."""
        if not self.client:
            raise ValueError("Groq API key not configured")
            
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant. Provide clear, concise, and helpful responses."
                },
                {
                    "role": "user",
                    "content": message,
                }
            ],
            model="llama3-8b-8192",
            temperature=0.7,
            max_tokens=1000
        )
        return chat_completion.choices[0].message.content


class GeminiProvider(AIProvider):
    """Google Gemini AI provider implementation."""
    
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None

    @retry(
        retry=retry_if_not_exception_type(ValueError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    def generate_response(self, message: str) -> str:
        """Generate response using Gemini."""
        if not self.model:
            raise ValueError("Gemini API key not configured")
            
        # Configure generation parameters
        generation_config = genai.types.GenerationConfig(
            temperature=0.7,
            max_output_tokens=1000,
            top_p=0.8,
            top_k=40
        )
        
        response = self.model.generate_content(
            message,
            generation_config=generation_config
        )
        return response.text
