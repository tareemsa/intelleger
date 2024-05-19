from rest_framework import status,views
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Project,Task
from .serializers import ProjectSerializer,UserSerializer,TaskSerializer,UpdateDevelopersSerializer
from .permissions import IsAdminUser  # Make sure to import the custom permission
from rest_framework import generics,permissions
from .models import CustomUser
from rest_framework.permissions import IsAuthenticated
from django.http import Http404
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from .ai_service import generate_ai_requirements  # AI service integration


class ProjectCreateView(generics.CreateAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        # Retrieve the project instance and scope from the serializer
        project = serializer.instance
        scope = serializer.validated_data['scope']

        # Generate AI requirements using the scope
        ai_requirements = generate_ai_requirements(scope)

        # Build the response data including project details and AI requirements
        response_data = {
            "project": ProjectSerializer(project, context={'request': request}).data,
            "ai_requirements": ai_requirements
        }

        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
        
class AcceptAIRequirementsView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, *args, **kwargs):
        project_id = request.data.get('project_id')
        ai_requirements = request.data.get('ai_requirements', [])

        project = Project.objects.get(pk=project_id)  # Handle DoesNotExist in production

        for req in ai_requirements['functional_requirements']:
            Task.objects.create(
                project=project,
                description=req['description'],
                status='Pending',
                deadline=req['deadline']  # Now using the deadline provided in the request
            )

        return Response({"message": "Tasks created from AI requirements."})



class EditAndSaveRequirementsView(APIView):
    permission_classes = [IsAuthenticated]
    permission_classes = [IsAuthenticated, IsAdminUser]
    def post(self, request, *args, **kwargs):
        project_id = request.data.get('project_id')
        edited_requirements = request.data.get('edited_requirements', [])

        project = Project.objects.get(pk=project_id)  # Handle DoesNotExist in production
        Task.objects.filter(project=project).delete()  # Clear previous AI tasks if any
        for req in edited_requirements:
            Task.objects.create(
                project=project,
                description=req['description'],
                status='Pending',
                deadline=req['deadline']  # Now using the deadline provided in the request
            )    
            
        return Response({"message": "Edited tasks saved."})

###############################

class ProjectListView(generics.ListAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filter projects to only those owned by the current user
        return Project.objects.filter(manager=self.request.user)

class ProjectDetailView(generics.RetrieveAPIView):
    #queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filter projects to only those owned by the current user
        return Project.objects.filter(manager=self.request.user)

class ProjectDevelopersListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if queryset is not None:
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                "status": "success",
                "message": "Developers fetched successfully.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": "error",
                "message": "You do not have permission to view the developers of this project."
            }, status=status.HTTP_403_FORBIDDEN)

    def get_queryset(self):
        """
        This view returns a list of all the developers assigned to a specific project,
        determined by the project ID in the URL.
        """
        project_id = self.kwargs['pk']
        try:
            project = Project.objects.get(id=project_id)
            # Check if the request user is the manager or part of the developers
            if self.request.user == project.manager or self.request.user in project.developers.all() or self.request.user.is_staff:
                return project.developers.all()
            return None  # User does not have permission
        except Project.DoesNotExist:
            raise Http404("Project not found.")


class ProjectAssignDevelopersView(generics.UpdateAPIView):
    queryset = Project.objects.all()
    serializer_class = UpdateDevelopersSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Override this method to ensure that only project managers can update the project.
        """
        try:
            project = Project.objects.get(id=self.kwargs['pk'])
            # Check if the request user is the manager
            if self.request.user == project.manager:
                return Project.objects.filter(id=project.id)
            # If not manager, raise a permission denied exception with a custom message
            raise PermissionDenied("You don't have permission to add developers to this project because it's not your own.")
        except Project.DoesNotExist:
            raise Http404("Project not found")

    def patch(self, request, *args, **kwargs):
        project = self.get_object()  # This checks permission and raises Http404 if not found or PermissionDenied if not allowed

        # Merge new developers with existing developers
        new_developer_ids = request.data.get('developers', [])
        if not isinstance(new_developer_ids, list):
            return Response({
                "status": "error",
                "message": "Invalid data format. 'developers' should be a list of developer IDs."
            }, status=status.HTTP_400_BAD_REQUEST)

        existing_developer_ids = list(project.developers.values_list('id', flat=True))
        all_developer_ids = list(set(existing_developer_ids + new_developer_ids))

        # Validate all developer IDs
        valid_developers = CustomUser.objects.filter(id__in=all_developer_ids, admin_role=False)
        if len(valid_developers) != len(all_developer_ids):
            return Response({
                "status": "error",
                "message": "Some developer IDs are invalid or not developers."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Update developers
        project.developers.set(valid_developers)
        project.save()

        return Response({
            "status": "success",
            "message": "Developers updated successfully.",
            "data": UpdateDevelopersSerializer(project).data
        }, status=status.HTTP_200_OK)
        
class ProjectUpdateView(generics.UpdateAPIView):
    
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        Override this method to include permission checks.
        Fetches the project only if the current user is its manager.
        """
        try:
            project = Project.objects.get(id=self.kwargs['pk'])
            if project.manager != self.request.user:
                raise PermissionDenied("You don't have permission to update this project because it's not your own.")
            return project
        except Project.DoesNotExist:
            raise Http404("Project not found")

    def patch(self, request, *args, **kwargs):
        project = self.get_object()  # Will handle permissions and raise if unauthorized
        serializer = self.get_serializer(project, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "message": "Project updated successfully.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": "error",
                "message": "Failed to update the project due to invalid data.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

class ProjectDeleteView(generics.DestroyAPIView):
    
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        Ensure that the project can only be deleted by its manager.
        """
        try:
            # Fetch the project if the current user is the manager
            project = Project.objects.get(id=self.kwargs['pk'], manager=self.request.user)
            return project
        except Project.DoesNotExist:
            raise Http404("Project not found")

    def delete(self, request, *args, **kwargs):
        try:
            response = self.destroy(request, *args, **kwargs)
            return Response({
                "status": "success",
                "message": "Project deleted successfully."
            }, status=response.status_code)
        except Http404:
            # Return a custom message if the project doesn't exist
            return Response({
                "status": "error",
                "message": "Project not found or you do not have permission to delete it."
            }, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied:
            # Return a custom permission denied message
            return Response({
                "status": "error",
                "message": "You do not have permission to delete this project because it's not your own."
            }, status=status.HTTP_403_FORBIDDEN)



class RemoveDeveloperView(generics.UpdateAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def patch(self, request, *args, **kwargs):
        project = self.get_object()  # Gets the project instance based on URL parameter 'pk'

        # Retrieve developer IDs from request data
        developer_ids = request.data.get('developers', [])
        if not developer_ids:
            return Response({'error': 'No developers specified'}, status=status.HTTP_400_BAD_REQUEST)

        # Filter developers who are actually part of this project
        developers_to_remove = project.developers.filter(id__in=developer_ids)

        if not developers_to_remove:
            return Response({'error': 'No valid developers found to remove'}, status=status.HTTP_404_NOT_FOUND)

        # Remove the developers
        project.developers.remove(*developers_to_remove)

        # Optionally, you can return the updated project data
        # project = self.get_object()  # Refresh the instance to reflect the removal
        # serializer = self.get_serializer(project)
        # return Response(serializer.data)

        return Response({'message': 'Developers removed successfully'}, status=status.HTTP_200_OK)



class TaskAssignView(generics.UpdateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'  # Custom lookup field

    def perform_create(self, serializer):
        task = self.get_object()
        project = task.project

        if self.request.user != project.manager:
            raise PermissionDenied("You are not authorized to assign tasks in this project.")

        developer_id = serializer.validated_data.get('developer').id
        if developer_id not in project.developers.values_list('id', flat=True):
            return Response({
                "error": "Developer is not part of this project's team."
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

