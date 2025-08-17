
# FastAPI Project with Multi-Tenant Auth and AI Chat

This project is a simple yet powerful FastAPI application that demonstrates a multi-tenant authentication system with SQLite, role-based access control (RBAC), and an AI-powered chat service using LangGraph, Groq, and Gemini.

## Features

- **FastAPI**: A modern, fast (high-performance) web framework for building APIs with Python 3.7+ based on standard Python type hints.
- **Pydantic V2**: Data validation and settings management using Python type annotations.
- **UV**: A fast, next-generation Python package manager.
- **Multi-Tenant Authentication**: Secure user signup and login with a multi-tenant architecture using SQLite and SQLAlchemy.
- **JWT-Based Security**: Secure authentication using JSON Web Tokens.
- **Role-Based Access Control (RBAC)**: Pre-defined user roles (admin, super_user, user) with different access levels.
- **AI Chat Service**: A flexible chat service powered by LangGraph that can switch between Groq and Gemini models based on configuration.
- **Business Module Structure**: A clean and organized project structure that promotes separation of concerns and maintainability.

## Getting Started

### Prerequisites

- Python 3.9+
- [UV](https://github.com/astral-sh/uv) installed

### Installation

1. **Clone the repository:**

   ```bash
   git clone <repository_url>
   cd <repository_directory>
   ```

2. **Create a virtual environment and install dependencies:**

   ```bash
   uv venv
   uv pip install -r requirements.txt
   ```

3. **Set up environment variables:**

   - Rename `.env.example` to `.env`.
   - Open the `.env` file and add your secret key and API keys for Groq and Gemini.

     ```env
     # General Settings
     PROJECT_NAME="FastAPI Project"
     API_V1_STR="/api/v1"

     # Security Settings
     SECRET_KEY="your_super_secret_key_here"
     ACCESS_TOKEN_EXPIRE_MINUTES=1440 # 1 day

     # AI Service Settings
     # Set AI_PROVIDER to 'groq' or 'gemini'
     AI_PROVIDER="gemini"

     # Add your API keys here
     GROQ_API_KEY="your_groq_api_key"
     GEMINI_API_KEY="your_gemini_api_key"
     ```

### Running the Application

To run the application, use the following command:

```bash
uvicorn src.main:app --reload
```

The API documentation will be available at `http://127.0.0.1:8000/docs`.

## API Endpoints

### Public Endpoints

- `GET /hello`: A public endpoint that returns a "Hello, world!" message.

### Authentication

- `POST /api/v1/signup`: Create a new user.
- `POST /api/v1/login/access-token`: Log in and receive a JWT access token.
- `POST /api/v1/password-recovery/{email}`: (Placeholder) Send a password recovery email.
- `POST /api/v1/reset-password/`: (Placeholder) Reset the user's password.
- `POST /api/v1/change-password/`: Change the current user's password.

### Protected Endpoints

- `GET /welcome`: A protected endpoint that requires JWT authentication.
- `GET /user/me`: An endpoint accessible only to authenticated users.
- `GET /superuser/me`: An endpoint accessible only to superusers and admins.
- `GET /admin/me`: An endpoint accessible only to admins.

### AI Chat Service

- `POST /api/v1/chat`: Chat with the AI service (requires authentication).

## Project Structure

```
src/
├── Backend/
│   ├── Auth/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── router.py
│   │   ├── schemas.py
│   │   └── services.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── security.py
│   ├── Shared/
│   │   ├── __init__.py
│   │   └── database.py
│   ├── ai-service/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── schemas.py
│   │   └── services.py
│   ├── ... (other feature modules)
│   └── __init__.py
├── __init__.py
└── main.py
