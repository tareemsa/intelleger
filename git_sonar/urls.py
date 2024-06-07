from django.urls import path, include
from .views import GitHubCallbackView, list_repositories

urlpatterns = [
    path('github/callback/', GitHubCallbackView.as_view(), name='github_callback'),
    path('repositories/', list_repositories, name='list_repositories'),

]
