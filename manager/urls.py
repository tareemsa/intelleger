from django.urls import path
from .views import ProjectCreateView

urlpatterns = [
    path('projects/', ProjectCreateView.as_view(), name='create-project'),
]
