from django.urls import path, include
from rest_framework.routers import SimpleRouter
from apps.moderation.views import ModerationQueueViewSet, ModerationHistoryViewSet

router = SimpleRouter(trailing_slash=False)
router.register(r'queue', ModerationQueueViewSet, basename='moderation-queue')
router.register(r'history', ModerationHistoryViewSet, basename='moderation-history')

app_name = 'moderation'

urlpatterns = [
    path('', include(router.urls)),
]


