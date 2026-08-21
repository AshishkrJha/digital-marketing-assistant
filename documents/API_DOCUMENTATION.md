# Conversational AI with Moderation Workflow - Complete Setup Guide

## 🎯 Project Overview

This is a production-ready conversational AI application with:
- **User Authentication**: JWT-based REST API with role-based access control
- **LLM Integration**: Google Gemini with LangChain for conversation memory management
- **Moderation Workflow**: Multi-level approval system for response validation
- **Multi-Project Support**: Users can create and manage multiple projects
- **CRM Integration**: Automatic webhook sync to third-party CRM on approval
- **Enterprise Architecture**: Follows Django best practices with modular app structure

---

## 📋 Tech Stack

- **Backend**: Django 6.0.5
- **API Framework**: Django REST Framework
- **Authentication**: JWT (djangorestframework-simplejwt)
- **LLM**: Google Gemini with LangChain
- **Database**: PostgreSQL (SQLite for development)
- **Server**: Waitress WSGI
- **Additional**: python-decouple, django-cors-headers, pydantic, requests

---

## 🚀 Quick Start

### 1. Prerequisites

```bash
python --version  # Python 3.12+
pip list          # Verify pip is available
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
```

**Required Environment Variables:**
- `GEMINI_API_KEY`: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- `CRM_WEBHOOK_URL`: Your CRM webhook endpoint
- `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`: PostgreSQL credentials (or use SQLite)
- `CORS_ALLOWED_ORIGINS`: Frontend URLs (localhost:3000 for development)

### 4. Initialize Database

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser (admin account)
python manage.py createsuperuser
```

### 5. Run Development Server

```bash
python manage.py runserver
```

Access the API at: `http://localhost:8000/api/`
Admin panel at: `http://localhost:8000/admin/`

---

## 📚 API Endpoints

### Authentication Endpoints

#### Register New User
```
POST /api/users/auth/register/
Content-Type: application/json

{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "securepassword123",
  "password_confirm": "securepassword123"
}

Response: 201 Created
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "user",
    "profile": {...}
  }
}
```

#### Login
```
POST /api/users/auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}

Response: 200 OK
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {...}
}
```

#### Get Current User Profile
```
GET /api/users/profile/
Authorization: Bearer <access_token>

Response: 200 OK
{
  "id": 1,
  "email": "user@example.com",
  "role": "user",
  "profile": {
    "phone": "...",
    "bio": "...",
    "department": "..."
  }
}
```

#### Update Profile
```
PUT /api/users/profile/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "profile": {
    "phone": "+1234567890",
    "bio": "Updated bio",
    "department": "Sales"
  }
}
```

#### Change Password
```
POST /api/users/change-password/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "old_password": "current_password",
  "new_password": "new_password",
  "confirm_password": "new_password"
}
```

---

### Projects Endpoints

#### List User's Projects
```
GET /api/projects/
Authorization: Bearer <access_token>

Response: 200 OK
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "name": "Project Alpha",
      "description": "First project",
      "owner": {...},
      "is_active": true,
      "created_at": "2026-05-25T10:00:00Z"
    }
  ]
}
```

#### Create Project
```
POST /api/projects/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "New Project",
  "description": "Project description"
}

Response: 201 Created
```

#### Get Project Details
```
GET /api/projects/{id}/
Authorization: Bearer <access_token>

Response: 200 OK
{
  "id": 1,
  "name": "Project Alpha",
  "members": [
    {
      "user": {...},
      "role": "member",
      "joined_at": "..."
    }
  ],
  "member_count": 5
}
```

#### Add Project Member
```
POST /api/projects/{id}/add_member/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "user_id": 5,
  "role": "member"
}

Response: 201 Created or 200 OK
```

#### Remove Project Member
```
DELETE /api/projects/{id}/remove_member/?user_id=5
Authorization: Bearer <access_token>

Response: 200 OK
```

---

### Conversations Endpoints

#### Create Conversation
```
POST /api/conversations/conversations/?project_id=1
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "Sales Strategy Discussion"
}

Response: 201 Created
{
  "id": 1,
  "title": "Sales Strategy Discussion",
  "user": {...},
  "message_count": 0,
  "created_at": "..."
}
```

#### Get Conversation Details
```
GET /api/conversations/conversations/{id}/
Authorization: Bearer <access_token>

Response: 200 OK
{
  "id": 1,
  "title": "...",
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "What is...",
      "timestamp": "..."
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "Based on...",
      "timestamp": "..."
    }
  ]
}
```

#### Generate LLM Response
```
POST /api/conversations/conversations/{id}/generate_response/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "message_content": "What are the best practices for sales?"
}

Response: 200 OK
{
  "user_message": {
    "id": 10,
    "role": "user",
    "content": "What are the best practices...",
    "timestamp": "..."
  },
  "assistant_message": {
    "id": 11,
    "role": "assistant",
    "content": "Best practices for sales include...",
    "timestamp": "..."
  }
}
```

#### Get Conversation Messages
```
GET /api/conversations/conversations/{id}/messages/
Authorization: Bearer <access_token>

Response: 200 OK
[
  {"id": 1, "role": "user", "content": "..."},
  {"id": 2, "role": "assistant", "content": "..."}
]
```

---

### Response & Moderation Endpoints

#### Submit Response for Moderation
```
POST /api/conversations/responses/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "message_id": 11,
  "content": "Final response to be moderated"
}

Response: 201 Created
{
  "id": 1,
  "content": "Final response...",
  "status": "submitted",
  "approval": null
}
```

#### Get User's Responses
```
GET /api/conversations/responses/
Authorization: Bearer <access_token>

Response: 200 OK
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "content": "...",
      "status": "approved",
      "approval": {
        "moderator": {...},
        "decision": "approved",
        "comments": "Looks good!",
        "crm_synced": true,
        "approved_at": "..."
      }
    }
  ]
}
```

#### Get Response Details
```
GET /api/conversations/responses/{id}/
Authorization: Bearer <access_token>

Response: 200 OK
{
  "id": 1,
  "content": "...",
  "status": "approved",
  "submitted_by": {...},
  "approval": {...}
}
```

---

### Moderation Queue (Moderator Only)

#### Get Pending Approvals
```
GET /api/moderation/queue/
Authorization: Bearer <moderator_token>

Response: 200 OK
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "response": {
        "id": 10,
        "content": "Response text...",
        "status": "submitted"
      },
      "user": {
        "id": 5,
        "email": "user@example.com",
        "name": "John Doe"
      },
      "project": {
        "id": 1,
        "name": "Project Alpha"
      },
      "status": "pending",
      "created_at": "..."
    }
  ]
}
```

#### Get Specific Approval Details
```
GET /api/moderation/queue/{id}/
Authorization: Bearer <moderator_token>

Response: 200 OK
{
  "id": 1,
  "response": {...},
  "user": {...},
  "project": {...},
  "logs": [
    {
      "moderator": {...},
      "action": "...",
      "timestamp": "..."
    }
  ]
}
```

#### Approve Response
```
POST /api/moderation/queue/{id}/approve/
Authorization: Bearer <moderator_token>
Content-Type: application/json

{
  "decision": "approved",
  "comments": "Approved - ready for CRM sync"
}

Response: 200 OK
{
  "message": "Response approved successfully",
  "crm_synced": true
}
```

#### Reject Response
```
POST /api/moderation/queue/{id}/reject/
Authorization: Bearer <moderator_token>
Content-Type: application/json

{
  "decision": "rejected",
  "comments": "Needs revision - grammar issues"
}

Response: 200 OK
{
  "message": "Response rejected successfully",
  "comments": "Needs revision - grammar issues"
}
```

#### View Moderation History (Admin Only)
```
GET /api/moderation/history/
Authorization: Bearer <admin_token>

Response: 200 OK
{
  "count": 100,
  "results": [
    {
      "id": 1,
      "response_id": 10,
      "moderator": {...},
      "user": {...},
      "action": "approved",
      "notes": "...",
      "timestamp": "..."
    }
  ]
}
```

---

## 🔐 Authentication

### JWT Token Usage

All authenticated endpoints require the `Authorization` header:

```
Authorization: Bearer <access_token>
```

### Token Refresh

```
POST /api/users/token/refresh/
Content-Type: application/json

{
  "refresh": "<refresh_token>"
}

Response: 200 OK
{
  "access": "<new_access_token>"
}
```

---

## 🎮 Testing the API

### Using cURL

```bash
# Register
curl -X POST http://localhost:8000/api/users/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123456",
    "password_confirm": "test123456"
  }'

# Login
curl -X POST http://localhost:8000/api/users/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123456"
  }'

# Create project (replace TOKEN)
curl -X POST http://localhost:8000/api/projects/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Project"}'
```

### Using Postman

1. Import API into Postman
2. Set `{{token}}` variable in environment
3. Add pre-request script to login and update token:

```javascript
pm.sendRequest({
    url: "http://localhost:8000/api/users/auth/login/",
    method: "POST",
    header: {
        "Content-Type": "application/json"
    },
    body: {
        mode: "raw",
        raw: JSON.stringify({
            email: "test@example.com",
            password: "test123456"
        })
    }
}, (err, response) => {
    if (!err) {
        pm.environment.set("token", response.json().access);
    }
});
```

---

## 🔧 Configuration

### Gemini LLM Setup

1. Get API key: https://makersuite.google.com/app/apikey
2. Add to `.env`:
   ```
   GEMINI_API_KEY=your-api-key-here
   GEMINI_MODEL=gemini-pro
   ```
3. Restart server

**LangChain Memory Management:**
- Conversation history is automatically loaded from database
- Supports buffer memory (default) or summary memory
- Configurable in settings: `LANGCHAIN_CONVERSATION_MEMORY_K` (default: 10 messages)

### CRM Webhook Configuration

Set in `.env`:
```
CRM_WEBHOOK_URL=https://your-crm.com/api/webhook
CRM_WEBHOOK_TIMEOUT=30
CRM_WEBHOOK_RETRY_ATTEMPTS=3
```

**Webhook Payload Structure:**
```json
{
  "user_id": "5",
  "user_email": "user@example.com",
  "project_id": "1",
  "project_name": "Project Alpha",
  "response_content": "The approved response text",
  "response_id": "10",
  "timestamp": "2026-05-25T15:30:00Z",
  "moderator_id": "2",
  "moderator_email": "moderator@example.com",
  "conversation_id": "3",
  "status": "approved"
}
```

---

## 👥 User Roles

### User Role
- Create conversations and projects
- Submit responses for moderation
- View their own responses and approval status
- Cannot access moderation queue

### Moderator Role
- View pending responses in moderation queue
- Approve or reject responses with comments
- View moderation history
- Cannot create conversations

### Admin Role
- Full access to all features
- Manage users and roles
- View complete moderation audit logs
- System administration

---

## 📊 Database Schema

### Key Models

**User**
- id, email, password, first_name, last_name, role
- related_name: conversations, owned_projects, submitted_responses

**Project**
- id, name, description, owner (FK), is_active, created_at

**Conversation**
- id, user (FK), project (FK), title, created_at
- related_name: message_set

**Message**
- id, conversation (FK), role (user/assistant), content, tokens_used

**Response**
- id, message (OneToOne), submitted_by (FK), content, status
- status: draft, submitted, approved, rejected

**ResponseApproval**
- id, response (OneToOne), moderator (FK), decision, comments, crm_synced

**ModerationQueue**
- id, response (OneToOne), status (pending/processed), created_at

---

## 🐛 Troubleshooting

### Migrations Failed
```bash
# Reset migrations (development only!)
python manage.py migrate zero  # Unapply all
python manage.py migrate       # Reapply
```

### Gemini API Errors
- Check API key in `.env`
- Verify API is enabled: https://console.cloud.google.com
- Check error logs in `logs/` directory

### Database Connection Errors
```bash
# For PostgreSQL
psql -U postgres -c "CREATE DATABASE conversationai;"

# For SQLite
rm db.sqlite3  # Delete and recreate
python manage.py migrate
```

### CORS Errors
Update `CORS_ALLOWED_ORIGINS` in `.env`:
```
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://yourfrontend.com
```

---

## 📦 Deployment

### Using Docker

```bash
docker-compose up -d
python manage.py migrate
python manage.py createsuperuser
```

### Using Waitress (Production)

```bash
waitress-serve --port=8000 emailPrepAI.wsgi:application
```

### Using Gunicorn

```bash
pip install gunicorn
gunicorn emailPrepAI.wsgi:application --workers 4 --bind 0.0.0.0:8000
```

---

## 📝 Logs

Logs are stored in `logs/` directory:
- `django.log` - General application logs
- `moderation.log` - Moderation actions
- `llm.log` - LLM integration logs

---

## 🤝 Contributing

When adding new features:
1. Create a new Django app: `python manage.py startapp feature_name`
2. Add to `INSTALLED_APPS` in settings.py
3. Create migrations: `python manage.py makemigrations`
4. Create serializers, views, and URLs
5. Add role-based permissions using `core/permissions.py`

---

## 📄 License

This project is built for ConversationAI system.

---

## 🆘 Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review error responses from API
3. Verify environment variables in `.env`
4. Check database connectivity

---

## ✅ Checklist Before Production

- [ ] Update `SECRET_KEY` in settings
- [ ] Set `DEBUG = False` in settings
- [ ] Configure `ALLOWED_HOSTS` for your domain
- [ ] Setup PostgreSQL database
- [ ] Setup Redis for caching (optional)
- [ ] Configure Gemini API key
- [ ] Setup CRM webhook URL
- [ ] Enable HTTPS
- [ ] Setup backup strategy
- [ ] Configure logging and monitoring
- [ ] Setup rate limiting
- [ ] Security headers (X-Frame-Options, CSP, etc.)
