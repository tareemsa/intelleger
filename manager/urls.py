from django.urls import path
from .views import  ProjectCreateView,TaskAssignView,ProjectListView,RemoveDeveloperView, ProjectDetailView, ProjectDevelopersListView, ProjectAssignDevelopersView,ProjectUpdateView,ProjectDeleteView
urlpatterns = [
    path('create_projects/', ProjectCreateView.as_view(), name='create-project'),
    path('view_projects/', ProjectListView.as_view(), name='project-list'),#view_all_projects
    path('view_projects_details/<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),#specific_project_details
    path('projects/<int:pk>/developers/', ProjectDevelopersListView.as_view(), name='developer-list'),
    path('projects/<int:pk>/assign-developers/', ProjectAssignDevelopersView.as_view(), name='assign-developers'),
    path('projects/<int:pk>/update/', ProjectUpdateView.as_view(), name='project-update'),
    path('projects/<int:pk>/delete/', ProjectDeleteView.as_view(), name='project-delete'),
    path('developers/<int:pk>/edit/', RemoveDeveloperView.as_view(), name='remove-developer'),
    path('projects/<int:project_id>/assign-task/', TaskAssignView.as_view(), name='assign-task'),

]



