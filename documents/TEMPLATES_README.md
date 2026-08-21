# Server-Rendered Templates Guide

## Overview

You now have a fully functional Django application with **server-rendered templates** that works alongside the REST API. The frontend is no longer a separate JavaScript-based Single Page Application (SPA), but rather traditional Django templates that render on the server.

## Architecture

### What Changed

**Before:** Pure REST API + separate frontend
- REST API endpoints returned JSON
- Frontend JavaScript app made HTTP requests
- No server-rendered HTML

**Now:** Server-Rendered Templates + REST API
- Django renders HTML templates on the server
- Users get a working web interface at `http://localhost:8000`
- REST API still available at `/api/` endpoints for mobile/external apps
- Session-based authentication for templates (login redirects)
- JWT tokens still work for API calls

## File Structure

```
templates/
├── base.html                      # Base template with navbar & sidebar
├── error.html                     # Error page
├── auth/
│   ├── login.html                # Login form (server-rendered)
│   └── register.html             # Registration form (server-rendered)
├── user/
│   ├── dashboard.html            # User dashboard
│   ├── projects.html             # List user projects
│   ├── project_detail.html       # Project details
│   ├── chat.html                 # Conversation chat interface
│   ├── responses.html            # User's responses history
│   └── profile.html              # User profile editor
├── moderator/
│   ├── dashboard.html            # Moderator stats
│   ├── queue.html                # Pending approvals queue
│   ├── review.html               # Review single response
│   └── history.html              # Moderation action logs
└── admin_panel/
    ├── dashboard.html            # Admin stats
    ├── users.html                # User management
    └── projects.html             # Project management
```

## Views & URL Routes

All frontend routes are at `/` (root path):

### Authentication
- `GET  /` or `/login/` → Login page
- `POST /login/` → Submit login form
- `GET  /register/` → Register page
- `POST /register/` → Submit registration form
- `GET  /logout/` → Logout user

### User Pages
- `GET /dashboard/` → User dashboard
- `GET /projects/` → List projects
- `GET /projects/<id>/` → Project details
- `GET /chat/` → Conversations list
- `GET /chat/<id>/` → View specific conversation
- `GET /my-responses/` → User's submitted responses
- `GET /profile/` → User profile
- `POST /profile/` → Update profile

### Moderator Pages
- `GET /moderator/` → Moderator dashboard
- `GET /moderator/queue/` → Pending approvals
- `GET /moderator/queue/<id>/review/` → Review response
- `GET /moderator/history/` → Moderation history

### Admin Pages
- `GET /admin-panel/` → Admin dashboard
- `GET /admin-panel/users/` → Manage users
- `GET /admin-panel/projects/` → View all projects

## How to Use

### 1. Start the Development Server

```bash
cd "c:\Ashish Jha\ashish-jha-github\ConversationAI\AIAssistance"
python manage.py runserver
```

The app runs at `http://localhost:8000`

### 2. Register a New User

1. Go to `http://localhost:8000/register/`
2. Fill in the registration form
3. Submit → creates user and logs them in
4. Redirects to dashboard

### 3. Login with Existing User

1. Go to `http://localhost:8000/login/`
2. Enter email & password
3. Submit → creates Django session
4. Redirects to dashboard based on role

### 4. Accessing Different Sections

**Regular Users:**
- View dashboard with projects and recent conversations
- Access projects and start conversations
- Submit responses for moderation
- View response status (pending/approved/rejected)
- Manage profile

**Moderators:**
- Access moderator dashboard
- Review pending responses in queue
- Approve/reject responses with comments
- View moderation history and audit logs

**Admins:**
- Access admin dashboard with system stats
- Manage users (change roles, activate/deactivate)
- View all projects
- Access Django admin at `/admin/` with Django's built-in admin interface

## Key Features Implemented

### Authentication
✅ Server-rendered login/register forms
✅ Django session-based authentication
✅ Password hashing with Django's authentication
✅ Role-based redirects (user → dashboard, moderator → queue, admin → admin panel)
✅ Logout functionality

### User Interface
✅ Responsive Bootstrap 5 design
✅ Sidebar navigation based on user role
✅ Dashboard with project/conversation stats
✅ Data-driven templates (actual database queries, not fake data)
✅ Error page for unauthorized access

### Views & Logic
✅ Database queries with `select_related()` for performance
✅ Permission checks with custom decorators
✅ Model method usage (`get_role_display()`, etc.)
✅ Form POST handling with Django's form validation
✅ Redirect-after-login pattern

### Moderation Workflow
✅ Moderator queue shows pending approvals
✅ Review page displays response with user context
✅ Approve/reject buttons with comment submission
✅ Moderation history tracks all actions
✅ Role-based access control

## Important Notes

### Session vs JWT
- **Server-rendered templates use Django sessions**
- **REST API uses JWT tokens** (`/api/` endpoints)
- They work independently - sessions are for web, JWT for APIs

### Database Requirements
The app uses the existing models:
- `User` (custom user model with role field)
- `UserProfile`
- `Project`, `UserProject`
- `Conversation`, `Message`, `Response`, `ResponseApproval`
- `ModerationQueue`, `ModerationLog`

Run migrations if you haven't already:
```bash
python manage.py migrate
```

### Creating Test Data
Create a superuser for testing:
```bash
python manage.py createsuperuser
```

Use this account to:
1. Login at `/`
2. Access admin panel at `/admin-panel/`
3. Manage users and view system stats

### Styling
- Uses Bootstrap 5 CDN
- Custom CSS in `static/css/style.css`
- Responsive design for mobile/tablet/desktop
- Dark sidebar with light content area

## Next Steps

### To Add Dynamic Features
1. **Conversations:** Implement chat message creation and LLM response generation
2. **Approvals:** Add AJAX/form submission for approve/reject without page reload
3. **Real-time Updates:** Use Django Channels for live queue updates for moderators

### To Integrate with REST API
The REST API still works! You can:
- Use token authentication at `/api/token/` 
- Call `/api/users/`, `/api/projects/`, etc. from external apps
- Build a separate React/Vue frontend that uses these API endpoints

### To Deploy
1. Set `DEBUG=False` in settings.py
2. Configure `ALLOWED_HOSTS`
3. Set up `SECRET_KEY` in environment
4. Use production database (PostgreSQL)
5. Serve with Gunicorn/uWSGI + Nginx
6. Collect static files: `python manage.py collectstatic`

## Troubleshooting

### "TemplateDoesNotExist" Error
- Ensure `templates/` folder exists in project root
- Check template path in view: `render(request, 'template.html')`
- Verify templates are in correct subdirectories

### "No such table" Error
- Run migrations: `python manage.py migrate`
- Check database file exists: `db.sqlite3`

### Login Redirects Not Working
- Check `INSTALLED_APPS` in settings.py includes all apps
- Verify URL patterns in `emailPrepAI/urls.py` and `apps/frontend/urls.py`
- Ensure `app_name = 'frontend'` is set in `apps/frontend/urls.py`

### 403 Forbidden on Moderator/Admin Pages
- Check user role: `User.role` must be 'moderator' or 'admin'
- Change role in Django admin at `/admin/`
- Or via admin panel at `/admin-panel/users/`

## Summary

Your application now has:
✅ Working server-rendered templates with real database data
✅ User authentication with Django sessions
✅ Role-based access control (user/moderator/admin)
✅ Fully functional admin, moderator, and user interfaces
✅ REST API still available for external apps
✅ Professional Bootstrap 5 design
✅ Production-ready code structure

**You can now access the web UI at `http://localhost:8000` without needing a separate frontend application!**
