
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Tuple
import os
from sqlalchemy.orm import Session
from src.backend.core.settings import settings
from groq import Groq
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential
from .models import ChatMessage

# Set API keys from settings
if settings.AI_PROVIDER == 'groq' and settings.GROQ_API_KEY:
    os.environ["GROQ_API_KEY"] = settings.GROQ_API_KEY

if settings.AI_PROVIDER == 'gemini' and settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

class GraphState(TypedDict):
    message: str
    response: str

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def call_groq(message: str) -> str:
    client = Groq()
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": message,
            }
        ],
        model="llama3-8b-8192",
    )
    return chat_completion.choices[0].message.content

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def call_gemini(message: str) -> str:
    model = genai.GenerativeModel('gemini-2.5-pro-preview-06-05')
    response = model.generate_content(message)
    return response.text

def get_response(state: GraphState) -> GraphState:
    message = state['message']
    if settings.AI_PROVIDER == 'groq':
        response = call_groq(message)
    elif settings.AI_PROVIDER == 'gemini':
        response = call_gemini(message)
    else:
        raise ValueError(f"Invalid AI_PROVIDER: {settings.AI_PROVIDER}")
    return {"message": message, "response": response}

workflow = StateGraph(GraphState)
workflow.add_node("get_response", get_response)
workflow.set_entry_point("get_response")
workflow.add_edge("get_response", END)

app = workflow.compile()

def run_chat(message: str) -> str:
    inputs = {"message": message}
    result = app.invoke(inputs)
    return result['response']

def save_chat_message(db: Session, user_id: int, message: str, response: str, provider: str) -> ChatMessage:
    """Save chat message to database."""
    chat_message = ChatMessage(
        user_id=user_id,
        message=message,
        response=response,
        provider=provider
    )
    db.add(chat_message)
    db.commit()
    db.refresh(chat_message)
    return chat_message

def run_chat_with_history(db: Session, user_id: int, message: str) -> Tuple[str, str]:
    """Run chat and save to history."""
    inputs = {"message": message}
    result = app.invoke(inputs)
    response = result['response']
    provider = settings.AI_PROVIDER
    
    # Save to database
    save_chat_message(db, user_id, message, response, provider)
    
    return response, provider

def get_chat_history(db: Session, user_id: int, skip: int = 0, limit: int = 50) -> list[ChatMessage]:
    """Get chat history for a user."""
    return db.query(ChatMessage).filter(
        ChatMessage.user_id == user_id
    ).order_by(ChatMessage.created_at.desc()).offset(skip).limit(limit).all()
