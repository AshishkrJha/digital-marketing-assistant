# Conversational AI with Moderation - Setup Instructions

## Quick Start (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings (at minimum):
# - GEMINI_API_KEY: Your Google Gemini API key
# - CORS_ALLOWED_ORIGINS: Your frontend URL
```

### 3. Initialize Database
```bash
# Create database tables
python manage.py migrate

# Create admin user
python manage.py createsuperuser
```

### 4. Start Development Server
```bash
python manage.py runserver

# Server runs at http://localhost:8000
# API: http://localhost:8000/api/
# Admin: http://localhost:8000/admin/
```

---

## Project Structure

```
emailPrepAI/                    # Project root
├── emailPrepAI/               # Main project config
│   ├── settings.py            # Django settings
│   ├── urls.py               # URL routing
│   ├── wsgi.py               # WSGI server config
│   └── asgi.py               # ASGI config
├── apps/                       # Django apps (modular)
│   ├── users/                 # Authentication & user management
│   ├── projects/              # Project management
│   ├── conversations/         # LLM conversations with LangChain
│   ├── moderation/            # Response approval workflow
│   └── integrations/          # Gemini LLM & CRM services
├── core/                       # Shared utilities
│   ├── permissions.py         # Role-based access control
│   ├── exceptions.py          # Custom exceptions
│   ├── utils.py              # Helper functions
│   └── routers.py            # DRF custom routers
├── logs/                       # Application logs
├── static/                     # Static files (CSS, JS)
├── templates/                  # HTML templates
├── manage.py                   # Django CLI
├── requirements.txt            # Python dependencies
├── docker-compose.yml          # Local PostgreSQL + Redis
├── Dockerfile                  # Container config
├── .env.example               # Environment template
├── API_DOCUMENTATION.md        # Complete API reference
└── README.md                   # Project overview
```

---

## Architecture Overview

### Tech Flow

```
User Login
    ↓
[JWT Authentication]
    ↓
Create Conversation
    ↓
User Input → LangChain Memory → Gemini LLM → Response
    ↓
User Submits Response
    ↓
[ModerationQueue Entry Created]
    ↓
Moderator Reviews
    ↓
├→ Approve → CRM Webhook Sync → Response Status: "approved"
└→ Reject → Store Comments → Response Status: "rejected"
    ↓
User Views Status
```

### Database Relationships

```
User (Custom extending Django User)
├── UserProfile (1-to-1)
├── Conversations (1-to-many)
│   └── Messages (1-to-many)
│       └── Response (1-to-1)
│           ├── ResponseApproval (1-to-1)
│           ├── ModerationQueue (1-to-1)
│           └── CRMLog (1-to-1)
├── Projects (owned_projects, 1-to-many)
│   ├── UserProject (many-to-many)
│   └── Conversations (1-to-many)
└── Roles: user, moderator, admin
```

---

## API Workflow Examples

### Example 1: User Conversation Flow

```bash
# 1. Register
POST /api/users/auth/register/
{"email": "user@example.com", "password": "..."}

# 2. Login
POST /api/users/auth/login/
{"email": "user@example.com", "password": "..."}
# Returns: access_token, refresh_token

# 3. Create Project
POST /api/projects/
Headers: Authorization: Bearer TOKEN
{"name": "Sales Proposals"}

# 4. Create Conversation
POST /api/conversations/conversations/?project_id=1
Headers: Authorization: Bearer TOKEN
{"title": "Q2 Sales Strategy"}

# 5. Generate LLM Response
POST /api/conversations/conversations/1/generate_response/
Headers: Authorization: Bearer TOKEN
{"message_content": "What are best practices for..."}

# 6. Submit for Moderation
POST /api/conversations/responses/
Headers: Authorization: Bearer TOKEN
{"message_id": 11, "content": "Final approved response"}

# 7. Check Status
GET /api/conversations/responses/1/
Headers: Authorization: Bearer TOKEN
# Shows status: approved/rejected with comments
```

### Example 2: Moderator Approval Flow

```bash
# 1. Login as Moderator
POST /api/users/auth/login/
{"email": "moderator@example.com", "password": "..."}

# 2. Get Pending Approvals
GET /api/moderation/queue/
Headers: Authorization: Bearer MODERATOR_TOKEN

# 3. Review Specific Response
GET /api/moderation/queue/1/
Headers: Authorization: Bearer MODERATOR_TOKEN

# 4a. Approve Response
POST /api/moderation/queue/1/approve/
Headers: Authorization: Bearer MODERATOR_TOKEN
{"decision": "approved", "comments": "Ready for CRM"}

# OR 4b. Reject Response
POST /api/moderation/queue/1/reject/
Headers: Authorization: Bearer MODERATOR_TOKEN
{"decision": "rejected", "comments": "Needs revision..."}
```

---

## LangChain Integration Details

### Memory Management

The system uses LangChain's `ConversationBufferMemory` to maintain conversation context:

```python
# From apps/integrations/llm_service.py

# Automatic conversation loading
load_conversation_history(conversation_id)

# Memory stores last 10 messages (configurable)
LANGCHAIN_CONVERSATION_MEMORY_K = 10

# User inputs and LLM responses automatically stored
```

### Custom Prompt Template

```
You are a helpful AI assistant. Provide thoughtful, accurate, and concise responses.

Previous conversation:
{chat_history}

User: {input}
Assistant:
```

### Configuration (in settings.py)

```python
LANGCHAIN_SETTINGS = {
    'verbose': DEBUG,
    'cache_type': 'memory',
    'temperature': 0.7,  # Creativity (0.0-1.0)
    'max_tokens': 1024,  # Response length limit
    'conversation_memory_type': 'buffer',  # or 'summary'
    'conversation_memory_k': 10,  # Messages to remember
}
```

---

## User Roles & Permissions

### Role Hierarchy

```
Admin
├── Full system access
├── Manage users and roles
├── View all moderation logs
└── System configuration

Moderator
├── View moderation queue (pending responses)
├── Approve/Reject responses with comments
├── View moderation history
├── Cannot create conversations or projects

Regular User
├── Create conversations and projects
├── Chat with LLM
├── Submit responses for moderation
├── View own responses and approval status
├── Cannot access moderation queue
└── Cannot approve responses
```

### Permission Classes (in core/permissions.py)

```python
IsUser              # role == 'user'
IsModerator         # role in ['moderator', 'admin']
IsAdmin             # role == 'admin'
IsConversationOwner # user owns conversation
IsProjectMember     # user is project member
IsResponseOwner     # user submitted response
```

---

## Development Workflow

### Adding a New Feature

```bash
# 1. Create Django app
python manage.py startapp feature_name

# 2. Define models in feature_name/models.py
# 3. Create serializers in feature_name/serializers.py
# 4. Create views in feature_name/views.py
# 5. Create URLs in feature_name/urls.py
# 6. Add permissions to core/permissions.py if needed

# 7. Make migrations
python manage.py makemigrations feature_name

# 8. Apply migrations
python manage.py migrate

# 9. Register in admin: feature_name/admin.py
```

### Testing Endpoint

```bash
# With curl
curl -X GET http://localhost:8000/api/endpoint/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"

# With Python requests
import requests
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("http://localhost:8000/api/endpoint/", headers=headers)
print(response.json())
```

---

## Environment Variables Reference

```ini
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
USE_SQLITE=True  # Set to False for PostgreSQL
DATABASE_NAME=conversationai
DATABASE_USER=postgres
DATABASE_PASSWORD=admin123
DATABASE_HOST=localhost
DATABASE_PORT=5432

# LLM Configuration
GEMINI_API_KEY=your-api-key-from-google
GEMINI_MODEL=gemini-pro

# CRM Webhook
CRM_WEBHOOK_URL=https://your-crm.com/webhook
CRM_WEBHOOK_TIMEOUT=30
CRM_WEBHOOK_RETRY_ATTEMPTS=3

# API/CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# LangChain
LANGCHAIN_VERBOSE=False
LANGCHAIN_TEMPERATURE=0.7
LANGCHAIN_CONVERSATION_MEMORY_K=10
```

---

## Common Commands

```bash
# Database
python manage.py migrate              # Apply migrations
python manage.py makemigrations       # Create migrations
python manage.py migrate zero         # Revert all (dev only)

# Users
python manage.py createsuperuser      # Create admin user
python manage.py changepassword user  # Change user password
python manage.py dumpdata > data.json # Backup data
python manage.py loaddata data.json   # Restore data

# Server
python manage.py runserver 0.0.0.0:8000  # Run on all interfaces
python manage.py shell                    # Django Python shell
python manage.py test                     # Run tests

# Maintenance
python manage.py collectstatic        # Collect static files
python manage.py check                # Check project for errors
```

---

## Logging

Logs are stored in `logs/` directory:

```
logs/
├── django.log       # General application logs
├── moderation.log   # Moderator approval actions
└── llm.log         # LLM API calls and responses
```

### View Logs

```bash
# Last 50 lines
tail -50 logs/django.log

# Follow live
tail -f logs/django.log

# Search for error
grep ERROR logs/django.log
```

---

## Docker Setup (Optional)

### Using Docker Compose for PostgreSQL

```bash
# Start PostgreSQL + Redis in background
docker-compose up -d

# Check status
docker-compose ps

# Stop services
docker-compose down
```

### Using Docker for Full Application

```bash
# Build image
docker build -t conversationai .

# Run container
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=your-key \
  -e DEBUG=False \
  conversationai

# Or with compose
docker-compose up --build
```

---

## Troubleshooting

### Issue: "psycopg2 could not connect"
**Solution:** Set `USE_SQLITE=True` in `.env` for development

### Issue: "ModuleNotFoundError: No module named 'django'"
**Solution:** Reinstall dependencies
```bash
pip install -r requirements.txt
```

### Issue: "GEMINI_API_KEY not configured"
**Solution:** Get key from https://makersuite.google.com/app/apikey and add to `.env`

### Issue: "Port 8000 already in use"
**Solution:** Use different port
```bash
python manage.py runserver 8001
```

### Issue: "Migration conflicts"
**Solution:** Reset migrations (development only)
```bash
python manage.py migrate zero
python manage.py migrate
```

---

## Performance Tips

1. **Conversation Memory**: Limit `LANGCHAIN_CONVERSATION_MEMORY_K` to avoid large context
2. **Database Indexing**: Indexes on frequently queried fields already configured
3. **Caching**: Consider adding Redis for session caching
4. **Rate Limiting**: Add rate limiting for API endpoints in production
5. **Pagination**: All list endpoints paginated at 20 results per page

---

## Security Checklist

- [ ] Change default `SECRET_KEY`
- [ ] Set `DEBUG = False` before production
- [ ] Use HTTPS in production
- [ ] Configure `ALLOWED_HOSTS` for your domain
- [ ] Enable CORS only for trusted origins
- [ ] Use strong database passwords
- [ ] Regularly rotate API keys
- [ ] Keep dependencies updated
- [ ] Use environment variables for secrets (no hardcoding)
- [ ] Setup proper logging and monitoring

---

## Next Steps

1. **Gemini API Setup**
   - Visit https://makersuite.google.com/app/apikey
   - Create API key
   - Add to `.env`: `GEMINI_API_KEY=your-key`

2. **Frontend Development**
   - Create React/Vue app on port 3000
   - Update `CORS_ALLOWED_ORIGINS` in `.env`
   - Use API endpoints from `API_DOCUMENTATION.md`

3. **CRM Integration**
   - Provide your CRM webhook URL
   - Update `CRM_WEBHOOK_URL` in `.env`
   - Approved responses will auto-sync

4. **Testing**
   - Test all endpoints with Postman/curl
   - Create test users and projects
   - Verify LLM responses and moderation flow

5. **Production Deployment**
   - Setup PostgreSQL database
   - Configure environment variables
   - Setup monitoring and logging
   - Deploy using Docker, Gunicorn, or Waitress

---

## Support Resources

- **Django Docs**: https://docs.djangoproject.com/
- **DRF**: https://www.django-rest-framework.org/
- **LangChain**: https://python.langchain.com/
- **Gemini API**: https://ai.google.dev/
- **JWT**: https://simplejwt.readthedocs.io/

---

## Summary

✅ **Complete System Ready!**

Your Conversational AI application with moderation workflow is now fully set up with:

- ✅ User authentication (JWT)
- ✅ Multi-project support
- ✅ LLM conversations with LangChain memory
- ✅ Moderator approval workflow
- ✅ CRM webhook integration
- ✅ Complete REST API
- ✅ Role-based access control
- ✅ Comprehensive logging

**Start the server and begin building your frontend!**
