from django.urls import path
from .views import (
 
    DeveloperTaskListView,
    DeveloperTaskDetailView, DeveloperProjectListView,RestartTaskView,ToDoRetrieveUpdateDestroyView ,ToDoListCreateView,GenerateCodeFromDescriptionView,DeveloperProjectDetailView,StartTaskView,CompleteTaskView
)

urlpatterns = [
  
    #path('personal-tasks/<int:pk>/', PersonalTaskDetailView.as_view(), name='personal-task-detail'),
    path('tasks/', DeveloperTaskListView.as_view(), name='developer-task-list'),
    path('tasks/<int:pk>/', DeveloperTaskDetailView.as_view(), name='developer-task-detail'),
    path('projects/', DeveloperProjectListView.as_view(), name='developer-project-list'),
    path('projects/<int:pk>/', DeveloperProjectDetailView.as_view(), name='developer-project-detail'),
    path('tasks/<int:pk>/start/', StartTaskView.as_view(), name='start-task'),
    path('tasks/<int:pk>/complete/', CompleteTaskView.as_view(), name='complete-task'),
    path('tasks/<int:pk>/RestartTask/', RestartTaskView.as_view(), name='Restart-task'),
    path('generate_code/', GenerateCodeFromDescriptionView.as_view(), name='generate-code'),
    path('todos/', ToDoListCreateView.as_view(), name='todo-list-create'),
    path('todos/<int:pk>/', ToDoRetrieveUpdateDestroyView.as_view(), name='todo-retrieve-update-destroy'),
]
