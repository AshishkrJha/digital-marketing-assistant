from django.urls import path
from apps.frontend import views

app_name = 'frontend'

urlpatterns = [
    # Auth
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login_alt'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # User
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('projects/', views.user_projects, name='user_projects'),
    path('projects/<int:project_id>/', views.user_project_detail, name='user_project_detail'),
    path('chat/', views.user_chat, name='user_chat'),
    path('chat/new/', views.create_conversation, name='create_conversation'),
    path('chat/<int:conversation_id>/', views.user_chat, name='user_chat_conversation'),
    path('my-responses/', views.user_responses, name='user_responses'),
    path('profile/', views.user_profile, name='user_profile'),

    # Moderator
    path('moderator/', views.moderator_dashboard, name='moderator_dashboard'),
    path('moderator/queue/', views.moderator_queue, name='moderator_queue'),
    path('moderator/queue/<int:queue_id>/review/', views.moderator_review, name='moderator_review'),
    path('moderator/history/', views.moderator_history, name='moderator_history'),

    # Admin Panel
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/users/', views.admin_users, name='admin_users'),
    path('admin-panel/projects/', views.admin_projects, name='admin_projects'),
]
