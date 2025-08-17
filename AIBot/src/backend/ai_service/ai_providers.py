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
            # Use the stable gemini-pro model instead of gemini-2.0-flash
            self.model = genai.GenerativeModel('gemini-2.5-pro-preview-06-05')
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
            
        try:
            # Use simpler generation config
            generation_config = {
                'temperature': 0.7,
                'max_output_tokens': 1000,
                'top_p': 0.8,
                'top_k': 40
            }
            
            response = self.model.generate_content(
                message,
                generation_config=generation_config
            )
            
            # Check if response was blocked or empty
            if not response.text:
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                    raise ValueError(f"Content generation blocked: {response.prompt_feedback}")
                else:
                    raise ValueError("Empty response from Gemini API")
                    
            return response.text.strip()
            
        except Exception as e:
            # Log the actual error for debugging
            print(f"Gemini API Error: {str(e)}")
            raise ValueError(f"Gemini API error: {str(e)}")
