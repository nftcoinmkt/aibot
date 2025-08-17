# FastAPI Multi-Tenant AI Project - Windsurf Instructions

## Project Overview
This is a FastAPI application with Pydantic V2, UV package manager, multi-tenant authentication, JWT-based security, role-based access control, and AI chat service powered by LangGraph with Groq/Gemini integration.

## Prerequisites
- Python 3.11+
- UV package manager
- SQLite (included with Python)

## Quick Start

### 1. Install UV Package Manager
```bash
# Install UV if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh
# or on Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Project Setup
```bash
# Clone or navigate to project directory
cd d:\AIBot

# Install dependencies using UV
uv sync

# Create environment file
cp .env.example .env

# Edit .env file with your API keys and settings
```

### 3. Environment Configuration
Edit `.env` file with your settings:
```env
# General Settings
PROJECT_NAME="FastAPI Multi-Tenant AI"
API_V1_STR="/api/v1"

# Database Settings
SQLALCHEMY_DATABASE_URI="sqlite:///./app.db"

# Security Settings
SECRET_KEY="your_super_secret_key_here_make_it_long_and_secure"
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ALGORITHM="HS256"

# AI Service Settings
AI_PROVIDER="gemini"  # or "groq"
GROQ_API_KEY="your_groq_api_key"
GEMINI_API_KEY="your_gemini_api_key"

# Email Settings (for password reset)
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=587
SMTP_USER="your_email@gmail.com"
SMTP_PASSWORD="your_app_password"
```

### 4. Run the Application
```bash
# Using UV
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Or activate virtual environment first
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
uvicorn src.main:app --reload
```

### 5. Access the Application
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/hello

## Project Structure

```
src/
├── Backend/
│   ├── core/                 # Core configuration and security
│   │   ├── config.py        # Settings and configuration
│   │   ├── security.py      # Password hashing and JWT
│   │   └── __init__.py
│   ├── Auth/                 # Authentication module
│   │   ├── models.py        # User and Tenant models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── services.py      # Business logic
│   │   ├── router.py        # API endpoints
│   │   └── __init__.py
│   ├── Shared/               # Shared utilities
│   │   ├── database.py      # Database connection
│   │   ├── email.py         # Email utilities
│   │   └── __init__.py
│   ├── ai_service/           # AI Chat service
│   │   ├── models.py        # Chat models
│   │   ├── schemas.py       # Chat schemas
│   │   ├── services.py      # LangGraph workflows
│   │   ├── router.py        # Chat endpoints
│   │   └── __init__.py
│   ├── feature1/             # Business feature modules
│   ├── feature2/
│   ├── Feature3/
│   └── Test/                 # Test scripts
├── main.py                   # FastAPI application entry point
└── __init__.py
```

## API Endpoints

### Public Endpoints
- `GET /hello` - Public hello endpoint (no authentication required)

### Authentication Endpoints
- `POST /api/v1/signup` - User registration
- `POST /api/v1/login/access-token` - User login
- `POST /api/v1/forgot-password` - Request password reset
- `POST /api/v1/reset-password` - Reset password with token
- `POST /api/v1/change-password` - Change password (authenticated)

### Protected Endpoints
- `GET /welcome` - Welcome message (any authenticated user)
- `GET /user/me` - User-specific endpoint
- `GET /superuser/me` - Super user endpoint
- `GET /admin/me` - Admin-only endpoint

### AI Chat Endpoints
- `POST /api/v1/chat` - Chat with AI (authenticated users)
- `GET /api/v1/chat/history` - Get chat history

### Admin Endpoints
- `GET /api/v1/users` - List all users (admin only)
- `POST /api/v1/users` - Create user (admin only)
- `PUT /api/v1/users/{user_id}` - Update user (admin only)
- `DELETE /api/v1/users/{user_id}` - Delete user (admin only)

## User Roles

### 1. **USER** (Default)
- Access to basic endpoints
- Can chat with AI
- Can change own password

### 2. **SUPER_USER**
- All USER permissions
- Access to super user endpoints
- Can view extended user information

### 3. **ADMIN**
- All SUPER_USER permissions
- Can create, update, delete other users
- Can manage user roles
- Full system access

## Multi-Tenant Architecture

The application supports multi-tenancy through:
- **Tenant Model**: Each user belongs to a tenant
- **Data Isolation**: Users can only access data within their tenant
- **Automatic Tenant Creation**: New tenants are created during user signup

## AI Chat Service

### Supported Providers
1. **Groq** - Fast inference with Llama models
2. **Gemini** - Google's AI model

### LangGraph Workflow
The chat service uses LangGraph for:
- Message processing
- Context management
- Response generation
- Chat history tracking

### Configuration
Switch between providers by setting `AI_PROVIDER` in `.env`:
```env
AI_PROVIDER="groq"    # or "gemini"
```

## Database Schema

### Users Table
- `id`: Primary key
- `email`: Unique email address
- `full_name`: User's full name
- `hashed_password`: Bcrypt hashed password
- `role`: User role (USER, SUPER_USER, ADMIN)
- `tenant_id`: Foreign key to tenant
- `is_active`: User status
- `created_at`: Creation timestamp

### Tenants Table
- `id`: Primary key
- `name`: Tenant name
- `created_at`: Creation timestamp

### Chat Messages Table
- `id`: Primary key
- `user_id`: Foreign key to user
- `message`: User message
- `response`: AI response
- `provider`: AI provider used
- `created_at`: Creation timestamp

## Testing

### Run Tests
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src

# Run specific test file
uv run pytest src/Backend/Test/test_auth.py
```

### Test Structure
- `test_auth.py` - Authentication tests
- `test_users.py` - User management tests
- `test_chat.py` - AI chat service tests
- `test_api.py` - API endpoint tests

## Development Workflow

### 1. Adding New Features
1. Create new module in appropriate business domain
2. Follow the structure: `models.py`, `schemas.py`, `services.py`, `router.py`
3. Add router to main application
4. Write tests

### 2. Database Migrations
```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head
```

### 3. Code Quality
```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .
```

## Security Features

### 1. Password Security
- Bcrypt hashing
- Minimum password requirements
- Password change functionality

### 2. JWT Tokens
- Secure token generation
- Configurable expiration
- Token validation middleware

### 3. Role-Based Access Control
- Hierarchical role system
- Endpoint-level authorization
- Tenant-based data isolation

### 4. Input Validation
- Pydantic V2 schemas
- Request/response validation
- SQL injection prevention

## Deployment

### 1. Production Setup
```bash
# Install production dependencies
uv sync --no-dev

# Set production environment variables
export ENVIRONMENT=production
export SECRET_KEY="your_production_secret"

# Run with Gunicorn
uv run gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 2. Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml .
RUN pip install uv && uv sync --no-dev

COPY . .
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all `__init__.py` files exist
   - Check Python path configuration

2. **Database Connection**
   - Verify SQLite file permissions
   - Check database URL in `.env`

3. **Authentication Issues**
   - Verify JWT secret key
   - Check token expiration settings

4. **AI Service Errors**
   - Validate API keys
   - Check provider configuration

### Debug Mode
```bash
# Run with debug logging
export LOG_LEVEL=DEBUG
uv run uvicorn src.main:app --reload --log-level debug
```

## API Usage Examples

### 1. User Registration
```bash
curl -X POST "http://localhost:8000/api/v1/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123",
    "full_name": "John Doe",
    "tenant_name": "acme-corp"
  }'
```

### 2. User Login
```bash
curl -X POST "http://localhost:8000/api/v1/login/access-token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=securepassword123"
```

### 3. Chat with AI
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how can you help me today?"
  }'
```

## Performance Considerations

### 1. Database Optimization
- Use database indexes for frequently queried fields
- Implement connection pooling for production
- Consider read replicas for scaling

### 2. Caching
- Implement Redis for session caching
- Cache AI responses for common queries
- Use CDN for static assets

### 3. Monitoring
- Add health check endpoints
- Implement logging and metrics
- Use APM tools for performance monitoring

## Contributing

### 1. Code Standards
- Follow PEP 8 style guide
- Use type hints throughout
- Write comprehensive docstrings
- Maintain test coverage above 80%

### 2. Git Workflow
- Create feature branches
- Write descriptive commit messages
- Submit pull requests for review
- Update documentation

This instruction document provides a complete guide for developing, deploying, and maintaining the FastAPI multi-tenant AI application using Windsurf IDE.
