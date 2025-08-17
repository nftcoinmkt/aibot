import os
from abc import ABC, abstractmethod
from groq import Groq
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_not_exception_type
from PIL import Image
import PyPDF2
from pathlib import Path

from src.backend.core.settings import settings


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    def generate_response(self, message: str) -> str:
        """Generate response from AI provider."""
        pass

    @abstractmethod
    def analyze_file(self, file_path: str, prompt: str) -> str:
        """Analyze a file (image or PDF) and generate response."""
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

    def analyze_file(self, file_path: str, prompt: str) -> str:
        """Groq doesn't support file analysis, so return a fallback message."""
        file_name = Path(file_path).name
        return f"I can see you've uploaded {file_name}. Unfortunately, I cannot analyze files directly with my current capabilities. Please describe what you'd like to know about this file, and I'll do my best to help!"


class GeminiProvider(AIProvider):
    """Google Gemini AI provider implementation."""
    
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            # Try different model names in order of preference
            model_names = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
            self.model = None
            for model_name in model_names:
                try:
                    self.model = genai.GenerativeModel(model_name)
                    print(f"Successfully initialized Gemini model: {model_name}")
                    break
                except Exception as e:
                    print(f"Failed to initialize model {model_name}: {str(e)}")
                    continue

            if not self.model:
                print("Failed to initialize any Gemini model")
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

    def analyze_file(self, file_path: str, prompt: str) -> str:
        """Analyze a file (image or PDF) using Gemini's multimodal capabilities."""
        if not self.model:
            raise ValueError("Gemini API key not configured")

        try:
            file_path = Path(file_path)
            file_extension = file_path.suffix.lower()

            if file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                # Handle image files
                return self._analyze_image(file_path, prompt)
            elif file_extension == '.pdf':
                # Handle PDF files
                return self._analyze_pdf(file_path, prompt)
            else:
                return f"I can see you've uploaded {file_path.name}. Unfortunately, I can only analyze images (JPG, PNG, GIF, etc.) and PDF files. Please upload a supported file type for analysis."

        except Exception as e:
            print(f"File analysis error: {str(e)}")
            return f"I encountered an error while analyzing {file_path.name}: {str(e)}"

    def _analyze_image(self, file_path: Path, prompt: str) -> str:
        """Analyze an image file using Gemini Vision."""
        try:
            # Load and prepare the image
            image = Image.open(file_path)

            # Create the prompt for image analysis
            analysis_prompt = f"{prompt}\n\nPlease provide a detailed analysis of this image."

            # Generate content with image
            response = self.model.generate_content([analysis_prompt, image])

            if not response.text:
                return f"I was able to process the image {file_path.name}, but couldn't generate a description. The image might contain content that I cannot analyze."

            return response.text.strip()

        except Exception as e:
            print(f"Image analysis error: {str(e)}")
            return f"I encountered an error while analyzing the image {file_path.name}: {str(e)}"

    def _analyze_pdf(self, file_path: Path, prompt: str) -> str:
        """Analyze a PDF file by extracting text and summarizing."""
        try:
            # Extract text from PDF
            text_content = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text_content += page.extract_text() + "\n"

            if not text_content.strip():
                return f"I was able to open {file_path.name}, but it appears to be empty or contains only images/scanned content that I cannot read."

            # Limit text length to avoid token limits
            max_chars = 8000  # Conservative limit
            if len(text_content) > max_chars:
                text_content = text_content[:max_chars] + "...\n[Document truncated due to length]"

            # Create analysis prompt
            analysis_prompt = f"{prompt}\n\nDocument content:\n{text_content}\n\nPlease provide a comprehensive summary and analysis."

            # Generate response
            response = self.model.generate_content(analysis_prompt)

            if not response.text:
                return f"I was able to read {file_path.name}, but couldn't generate a summary. The content might be too complex or contain unsupported elements."

            return response.text.strip()

        except Exception as e:
            print(f"PDF analysis error: {str(e)}")
            return f"I encountered an error while analyzing the PDF {file_path.name}: {str(e)}"
