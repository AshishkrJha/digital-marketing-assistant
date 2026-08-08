from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from apps.users.models import User, UserProfile
from apps.projects.models import Project, UserProject
from apps.conversations.models import Conversation, Message, Response, ResponseApproval
from apps.moderation.models import ModerationQueue, ModerationLog


def login_required_decorator(view_func):
    """Custom decorator for template-based views"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('frontend:login')
        return view_func(request, *args, **kwargs)
    return wrapper


def moderator_required(view_func):
    """Decorator to check if user is moderator or admin"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('frontend:login')
        if request.user.role not in ['moderator', 'admin']:
            return render(request, 'error.html', {'error': 'You do not have permission to access this page.'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    """Decorator to check if user is admin"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('frontend:login')
        if request.user.role != 'admin':
            return render(request, 'error.html', {'error': 'Admin access required.'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


# ── Auth ──────────────────────────────────────────────────────────────────────

@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('frontend:user_dashboard')
        else:
            return render(request, 'auth/login.html', {'error': 'Invalid email or password.'})

    return render(request, 'auth/login.html')


@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        if password != password_confirm:
            return render(request, 'auth/register.html', {'error': 'Passwords do not match.'})

        if User.objects.filter(email=email).exists():
            return render(request, 'auth/register.html', {'error': 'Email already registered.'})

        user = User.objects.create_user(
            email=email,
            username=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            role='user'
        )

        UserProfile.objects.create(user=user)

        login(request, user)
        return redirect('frontend:user_dashboard')

    return render(request, 'auth/register.html')


@login_required(login_url='frontend:login')
def logout_view(request):
    logout(request)
    return redirect('frontend:login')


# ── User ──────────────────────────────────────────────────────────────────────

@login_required_decorator
def user_dashboard(request):
    user_projects = UserProject.objects.filter(user=request.user).select_related('project')
    recent_conversations = Conversation.objects.filter(user=request.user).order_by('-updated_at')[:5]

    context = {
        'projects': user_projects,
        'recent_conversations': recent_conversations,
    }
    return render(request, 'user/dashboard.html', context)


@login_required_decorator
def user_projects(request):
    user_projects = UserProject.objects.filter(user=request.user).select_related('project')

    context = {
        'projects': user_projects,
    }
    return render(request, 'user/projects.html', context)


@login_required_decorator
def user_project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    user_project = UserProject.objects.filter(user=request.user, project=project).first()
    if not user_project:
        return render(request, 'error.html', {'error': 'You do not have access to this project.'}, status=403)

    conversations = Conversation.objects.filter(project=project, user=request.user)

    context = {
        'project': project,
        'conversations': conversations,
        'user_role': user_project.role,
    }
    return render(request, 'user/project_detail.html', context)


@login_required_decorator
def user_chat(request, conversation_id=None):
    if conversation_id:
        conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
        messages = Message.objects.filter(conversation=conversation).order_by('timestamp')
    else:
        conversation = None
        messages = []

    user_conversations = Conversation.objects.filter(user=request.user).select_related('project').order_by('-updated_at')
    user_projects = Project.objects.filter(members__user=request.user, is_active=True)

    context = {
        'conversation': conversation,
        'messages': messages,
        'conversations': user_conversations,
        'user_projects': user_projects,
    }
    return render(request, 'user/chat.html', context)


@login_required_decorator
@require_http_methods(['POST'])
def create_conversation(request):
    project_id = request.POST.get('project_id')
    title = request.POST.get('title', '').strip() or 'New Conversation'

    project = get_object_or_404(Project, id=project_id, members__user=request.user, is_active=True)
    conversation = Conversation.objects.create(
        user=request.user,
        project=project,
        title=title,
    )
    return redirect('frontend:user_chat_conversation', conversation_id=conversation.id)


@login_required_decorator
def user_responses(request):
    responses = Response.objects.filter(submitted_by=request.user).select_related(
        'message__conversation', 'approval'
    ).order_by('-created_at')

    context = {
        'responses': responses,
    }
    return render(request, 'user/responses.html', context)


@login_required_decorator
def user_profile(request):
    profile = UserProfile.objects.get(user=request.user)

    if request.method == 'POST':
        profile.phone = request.POST.get('phone', profile.phone)
        profile.bio = request.POST.get('bio', profile.bio)
        profile.department = request.POST.get('department', profile.department)
        profile.save()

        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.last_name = request.POST.get('last_name', request.user.last_name)
        request.user.save()

        return render(request, 'user/profile.html', {'profile': profile, 'message': 'Profile updated successfully.'})

    context = {
        'profile': profile,
    }
    return render(request, 'user/profile.html', context)


# ── Moderator ─────────────────────────────────────────────────────────────────

@moderator_required
def moderator_dashboard(request):
    pending_count = ModerationQueue.objects.filter(status='pending').count()
    processed_count = ModerationQueue.objects.filter(status='processed').count()
    recent_actions = ModerationLog.objects.order_by('-timestamp')[:10]

    context = {
        'pending_count': pending_count,
        'processed_count': processed_count,
        'recent_actions': recent_actions,
    }
    return render(request, 'moderator/dashboard.html', context)


@moderator_required
def moderator_queue(request):
    queue_items = ModerationQueue.objects.filter(status='pending').select_related(
        'response__message__conversation__user',
        'response__submitted_by',
    ).order_by('created_at')

    context = {
        'queue_items': queue_items,
    }
    return render(request, 'moderator/queue.html', context)


@moderator_required
def moderator_review(request, queue_id):
    queue_item = get_object_or_404(ModerationQueue, id=queue_id)
    response = queue_item.response
    message = response.message
    conversation = message.conversation

    context = {
        'queue_item': queue_item,
        'response': response,
        'message': message,
        'conversation': conversation,
        'user': conversation.user,
    }
    return render(request, 'moderator/review.html', context)


@moderator_required
def moderator_history(request):
    logs = ModerationLog.objects.select_related(
        'response__submitted_by',
        'moderator',
    ).order_by('-timestamp')

    context = {
        'logs': logs,
    }
    return render(request, 'moderator/history.html', context)


# ── Admin Panel ───────────────────────────────────────────────────────────────

@admin_required
def admin_dashboard(request):
    total_users = User.objects.count()
    total_projects = Project.objects.count()
    total_conversations = Conversation.objects.count()
    pending_approvals = ModerationQueue.objects.filter(status='pending').count()

    context = {
        'total_users': total_users,
        'total_projects': total_projects,
        'total_conversations': total_conversations,
        'pending_approvals': pending_approvals,
    }
    return render(request, 'admin_panel/dashboard.html', context)


@admin_required
def admin_users(request):
    users = User.objects.all().select_related('profile').order_by('-created_at')

    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        user = get_object_or_404(User, id=user_id)

        if action == 'change_role':
            new_role = request.POST.get('new_role')
            if new_role in ['user', 'moderator', 'admin']:
                user.role = new_role
                user.save()

        elif action == 'deactivate':
            user.is_active = False
            user.save()

        elif action == 'activate':
            user.is_active = True
            user.save()

        users = User.objects.all().select_related('profile').order_by('-created_at')

    context = {
        'users': users,
    }
    return render(request, 'admin_panel/users.html', context)


@admin_required
def admin_projects(request):
    projects = Project.objects.all().select_related('owner').order_by('-created_at')

    context = {
        'projects': projects,
    }
    return render(request, 'admin_panel/projects.html', context)
