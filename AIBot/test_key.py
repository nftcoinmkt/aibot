import os
import google.generativeai as genai
from dotenv import load_dotenv
"""
Model found: models/gemini-1.5-pro-latest
Model found: models/gemini-1.5-pro-002
Model found: models/gemini-1.5-pro
Model found: models/gemini-1.5-flash-latest
Model found: models/gemini-1.5-flash
Model found: models/gemini-1.5-flash-002
Model found: models/gemini-1.5-flash-8b
Model found: models/gemini-1.5-flash-8b-001
Model found: models/gemini-1.5-flash-8b-latest
Model found: models/gemini-2.5-pro-preview-03-25
Model found: models/gemini-2.5-flash-preview-05-20
Model found: models/gemini-2.5-flash
Model found: models/gemini-2.5-flash-lite-preview-06-17        
Model found: models/gemini-2.5-pro-preview-05-06
Model found: models/gemini-2.5-pro-preview-06-05
Model found: models/gemini-2.5-pro
Model found: models/gemini-2.0-flash-exp
Model found: models/gemini-2.0-flash
Model found: models/gemini-2.0-flash-001
Model found: models/gemini-2.0-flash-exp-image-generation
Model found: models/gemini-2.0-flash-lite-001
Model found: models/gemini-2.0-flash-lite
Model found: models/gemini-2.0-flash-preview-image-generation  
Model found: models/gemini-2.0-flash-lite-preview-02-05        
Model found: models/gemini-2.0-flash-lite-preview
Model found: models/gemini-2.0-pro-exp
Model found: models/gemini-2.0-pro-exp-02-05
Model found: models/gemini-exp-1206
Model found: models/gemini-2.0-flash-thinking-exp-01-21        
Model found: models/gemini-2.0-flash-thinking-exp
Model found: models/gemini-2.0-flash-thinking-exp-1219
Model found: models/gemini-2.5-flash-preview-tts
Model found: models/gemini-2.5-pro-preview-tts
Model found: models/learnlm-2.0-flash-experimental
Model found: models/gemma-3-1b-it
Model found: models/gemma-3-4b-it
Model found: models/gemma-3-12b-it
Model found: models/gemma-3-27b-it
Model found: models/gemma-3n-e4b-it
Model found: models/gemma-3n-e2b-it
Model found: models/gemini-2.5-flash-lite
"""
# Load environment variables from .env file
load_dotenv()

def test_gemini_connection():
    try:
        # Get API key from environment 
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Error: GEMINI_API_KEY not found in environment variables")
            return False
            
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Test connection with gemini-2.0-flash model
        print("Testing Gemini 2.0 Flash connection...")
        
        # Initialize the model
        model = genai.GenerativeModel('gemini-2.5-pro-preview-06-05')
        
        # Test a simple prompt
        response = model.generate_content("Say 'Hello' to test the connection")
        
        print("\nSuccessfully connected to Gemini 2.0 Flash!")
        print("\nTest response:")
        print(response.text)
        
        return True
        
    except Exception as e:
        print(f"Error connecting to Gemini API: {e}")
        return False

if __name__ == "__main__":
    test_gemini_connection()