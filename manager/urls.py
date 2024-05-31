from django.urls import path
from .views import  AssignDevelopersToTaskView,EvaluateRiskLevelView,CreateTaskView,DeleteTaskView,AcceptAIRequirementsView,ProjectCreateView,ProjectListView,RemoveDeveloperView, ProjectDetailView, ProjectDevelopersListView, ProjectAssignDevelopersView,ProjectUpdateView,ProjectDeleteView,EditAndSaveRequirementsView,EditTaskView,RemoveDevelopersFromTaskView,ListTasksForProjectView
urlpatterns = [
    path('create_project/', ProjectCreateView.as_view(), name='project-create'),
    path('projects/<int:project_id>/accept-requirements/', AcceptAIRequirementsView.as_view(), name='accept-ai-requirements'),
    path('projects/<int:project_id>/edit-requirements/', EditAndSaveRequirementsView.as_view(), name='edit-and-save-requirements'),
    path('view_projects/', ProjectListView.as_view(), name='project-list'),#view_all_projects
    path('view_projects_details/<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),#specific_project_details
    path('projects/<int:pk>/developers/', ProjectDevelopersListView.as_view(), name='developer-list'),#List_all_developers_for_specific_project
    path('projects/<int:pk>/assign-developers/', ProjectAssignDevelopersView.as_view(), name='assign-developers'),#assign_developers_to_project
    path('projects/<int:pk>/update/', ProjectUpdateView.as_view(), name='project-update'),
    path('projects/<int:pk>/delete/', ProjectDeleteView.as_view(), name='project-delete'),
    path('developers/<int:pk>/remove/', RemoveDeveloperView.as_view(), name='remove-developer'),#remove_developers_from_project
    path('projects/<int:project_id>/tasks/', ListTasksForProjectView.as_view(), name='list_tasks_for_project'),#list_all_this_project_tasks
    #########TASK########
    path('projects/<int:project_id>/tasks/create/', CreateTaskView.as_view(), name='create_task'),
    path('projects/<int:project_id>/tasks/<int:task_id>/assign/', AssignDevelopersToTaskView.as_view(), name='assign_developers_to_task'),#assign_developers_to_task
    path('projects/<int:project_id>/tasks/<int:task_id>/edit/', EditTaskView.as_view(), name='task-edit'),
    path('projects/<int:project_id>/tasks/<int:task_id>/remove_developers/', RemoveDevelopersFromTaskView.as_view(), name='remove_developers_from_task'),#Remove_developers_from_task
    path('projects/<int:project_id>/tasks/<int:task_id>/delete/', DeleteTaskView.as_view(), name='delete_task'),
    ###########risk_level############
    path('evaluate-risk/<int:project_id>/', EvaluateRiskLevelView.as_view(), name='evaluate-risk'),
]



