from django.urls import path, include
from rest_framework.routers import SimpleRouter
from apps.projects.views import ProjectViewSet

router = SimpleRouter(trailing_slash=False)
router.register(r'', ProjectViewSet, basename='project')

app_name = 'projects'

urlpatterns = [
    path('', include(router.urls)),
]



