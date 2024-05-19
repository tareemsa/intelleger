from django.urls import path
from .views import  TaskAssignView,AcceptAIRequirementsView,ProjectCreateView,ProjectListView,RemoveDeveloperView, ProjectDetailView, ProjectDevelopersListView, ProjectAssignDevelopersView,ProjectUpdateView,ProjectDeleteView,EditAndSaveRequirementsView
urlpatterns = [
    path('create_project/', ProjectCreateView.as_view(), name='project-create'),
    path('accept_ai_requirements/', AcceptAIRequirementsView.as_view(), name='accept-ai-requirements'),
    path('edit_and_save_requirements/', EditAndSaveRequirementsView.as_view(), name='edit-and-save-requirements'),
    path('view_projects/', ProjectListView.as_view(), name='project-list'),#view_all_projects
    path('view_projects_details/<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),#specific_project_details
    path('projects/<int:pk>/developers/', ProjectDevelopersListView.as_view(), name='developer-list'),
    path('projects/<int:pk>/assign-developers/', ProjectAssignDevelopersView.as_view(), name='assign-developers'),
    path('projects/<int:pk>/update/', ProjectUpdateView.as_view(), name='project-update'),
    path('projects/<int:pk>/delete/', ProjectDeleteView.as_view(), name='project-delete'),
    path('developers/<int:pk>/edit/', RemoveDeveloperView.as_view(), name='remove-developer'),
    path('projects/<int:project_id>/tasks/<int:id>/assign/', TaskAssignView.as_view(), name='assign-task'),

]



