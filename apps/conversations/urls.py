from django.urls import path, include
from rest_framework.routers import SimpleRouter
from apps.conversations.views import ConversationViewSet, ResponseViewSet

router = SimpleRouter(trailing_slash=False)
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'responses', ResponseViewSet, basename='response')

app_name = 'conversations'

urlpatterns = [
    path('', include(router.urls)),
]


