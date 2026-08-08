from django.urls import path, include
from rest_framework.routers import SimpleRouter
from apps.users.views import AuthViewSet, UserViewSet

router = SimpleRouter(trailing_slash=False)
router.register(r'', UserViewSet, basename='user')

app_name = 'users'

auth_patterns = [
    path('register/', AuthViewSet.as_view({'post': 'register'}), name='register'),
    path('login/', AuthViewSet.as_view({'post': 'login'}), name='login'),
    path('logout/', AuthViewSet.as_view({'post': 'logout'}), name='logout'),
]

urlpatterns = [
    path('auth/', include(auth_patterns)),
    path('profile/', UserViewSet.as_view({'get': 'profile', 'put': 'profile'}), name='profile'),
    path('change-password/', UserViewSet.as_view({'post': 'change_password'}), name='change_password'),
    path('', include(router.urls)),
]



