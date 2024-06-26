from rest_framework import status,views
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Project,Task,DeveloperMetrics
from .serializers import ProjectSerializer,UserSerializer,TaskSerializer
from .permissions import IsAdminUser  # Make sure to import the custom permission
from rest_framework import generics,permissions,serializers
from .models import CustomUser
from rest_framework.permissions import IsAuthenticated
from django.http import Http404    
from rest_framework.exceptions import PermissionDenied,NotFound
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from .ai_service import generate_requirements,evaluate_risk_level # AI service integration
from django.db.models import  Avg,Sum, F, ExpressionWrapper, DurationField
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

#########################PROJECT#########################

 # AI service integration

class ProjectCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def post(self, request):
        project_serializer = ProjectSerializer(data=request.data, context={'request': request})
        if project_serializer.is_valid():
            project = project_serializer.save()

            # Generate requirements
            functional_requirements, non_functional_requirements = generate_requirements(project.scope)
            
            # Save the generated requirements in the project instance
            project.functional_requirements = functional_requirements
            project.non_functional_requirements = non_functional_requirements
            project.save()

            response_data = {
                "project": project_serializer.data,
                "functional_requirements": functional_requirements,
                "non_functional_requirements": non_functional_requirements,
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response(project_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AcceptAIRequirementsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def post(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)

        functional_requirements = project.functional_requirements  # Use saved requirements

        for fr in functional_requirements:
            Task.objects.create(project=project, title=fr)

        return Response({"message": "Tasks created successfully"}, status=status.HTTP_200_OK)



class EditAndSaveRequirementsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def post(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)

        functional_requirements = request.data.get('functional_requirements', [])
        non_functional_requirement = request.data.get('non_functional_requirements', [])

        # Validate and save the edited requirements
        project.edited_functional_requirements = functional_requirements
        project.edited_non_functional_requirements = non_functional_requirement
        project.save()

        # Update tasks based on edited functional requirements
        Task.objects.filter(project=project).delete()  # Clear existing tasks
        for fr in functional_requirements:
            Task.objects.create(project=project, title=fr)

        return Response({"message": "Tasks created successfully"}, status=status.HTTP_200_OK)


#view_all_projects

class ProjectListView(generics.ListAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filter projects to only those owned by the current user
        return Project.objects.filter(manager=self.request.user)

#view_project_details

class ProjectDetailView(generics.RetrieveAPIView):
    #queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filter projects to only those owned by the current user
        return Project.objects.filter(manager=self.request.user)

#view_project_developers
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

#assign_developer_to_project
class ProjectAssignDevelopersView(generics.UpdateAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
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

        new_developer_emails = request.data.get('developers', [])
        developers_to_add = CustomUser.objects.filter(email__in=new_developer_emails)
        if not isinstance(new_developer_emails, list):
            return Response({
                "status": "error",
                "message": "Invalid data format. 'developers' should be a list of developer em."
            }, status=status.HTTP_400_BAD_REQUEST)

        existing_developer_email = list(project.developers.values_list('email', flat=True))
        all_developer_email = list(set(existing_developer_email + new_developer_emails))

        # Validate all developer IDs
        valid_developers = CustomUser.objects.filter(email__in=all_developer_email, admin_role=False)
        if len(valid_developers) != len(all_developer_email):
            return Response({
                "status": "error",
                "message": "Some developer email's are invalid or not developers."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Update developers
        project.developers.set(valid_developers)
        project.save()

        return Response({
            "status": "success",
            "message": "Developers updated successfully.",
            "data": ProjectSerializer(project).data
        }, status=status.HTTP_200_OK)
        
#update_project_details
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
#delete_project
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

    def delete(self, request, *args, **kwargs):
        project = self.get_object()  # Gets the project instance based on URL parameter 'pk'

        # Retrieve developer emails from request data
        developer_emails = request.data.get('developers', [])
        if not developer_emails:
            return Response({'error': 'No developers specified'}, status=status.HTTP_400_BAD_REQUEST)

        # Filter developers who are actually part of this project
        developers_to_remove = project.developers.filter(email__in=developer_emails)

        if not developers_to_remove:
            return Response({'error': 'No valid developers found to remove'}, status=status.HTTP_404_NOT_FOUND)

        # Remove the specified developers from the project
        for developer in developers_to_remove:
            project.developers.remove(developer)

        return Response({'message': 'Developers removed successfully'}, status=status.HTTP_200_OK)



#view_project_tasks
class ListTasksForProjectView(generics.ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        project_id = self.kwargs.get('project_id')
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            raise NotFound(detail="Project not found.")

        if project.manager != self.request.user:
            raise PermissionDenied(detail="You do not have permission to view tasks for this project.")

        return Task.objects.filter(project=project)







class ListProjectsForGanttChartView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(manager=user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        project_data = []

        for project in queryset:
            end_date = project.deadline
            start_date = project.created_at
            remaining_days = (end_date.date() - timezone.now().date()).days
            total_duration = (end_date.date() - start_date.date()).days
            elapsed_days = (timezone.now().date() - start_date.date()).days
            percentage_elapsed = round((elapsed_days / total_duration) * 100) if total_duration > 0 else 0

            if remaining_days < 0:
                status = 'Completed'
                remaining_days = 0
                percentage_elapsed = 100
            else:
                status = 'In Progress'

            project_data.append({
                'id': project.id,
                'name': project.name,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'remaining_days': remaining_days,
                'status': status,
                'percentage_elapsed': percentage_elapsed
            })

        return Response(project_data, status=200)

#########################TASK#########################

class CreateTaskView(generics.CreateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def perform_create(self, serializer):
        project_id = self.kwargs.get('project_id')
        
        try:
            project = Project.objects.get(id=project_id, manager=self.request.user)
        except Project.DoesNotExist:
            raise NotFound(detail="Project not found or you do not have permission to create tasks for this project.")
        
        # Get the developer's email from the request data
        developer_email = self.request.data.get('developer')
        try:
            # Retrieve the developer object based on the email
            developer = CustomUser.objects.get(email=developer_email)
        except CustomUser.DoesNotExist:
            raise ValidationError({'developer': ['No developer found with this email.']})
        
        # Save the task with the project and developer
        serializer.save(project=project, developer=developer)

        # Send notification to the developer
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notifications_{developer.id}',
            {
                'type': 'send_notification',
                'notification': f'You have been assigned a new task: '
            }
        )

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            return Response({
                'status': 'success',
                'message': 'Task created successfully'
            }, status=status.HTTP_201_CREATED)
        return response

        #############################################################################################

 
        
        ############################################################################################
class AssignDevelopersToTaskView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, project_id, task_id):
        try:
            project = Project.objects.get(id=project_id, manager=request.user)
            task = Task.objects.get(id=task_id, project=project)
        except Project.DoesNotExist:
            return Response({"detail": "Project not found or you do not have permission."}, status=404)
        except Task.DoesNotExist:
            return Response({"detail": "Task not found in this project."}, status=404)

        developer_email = request.data.get('developer', None)
        
        if not developer_email:
            return Response({"detail": "No developer provided to assign to the task."}, status=400)

        developer = CustomUser.objects.filter(email=developer_email).first()

        if not developer:
            return Response({"detail": f"Developer with email {developer_email} not found."}, status=400)

        if developer not in project.developers.all():
            return Response({"detail": f"Developer {developer_email} is not assigned to this project."}, status=400)

        task.developer = developer
        task.save()

        return Response(TaskSerializer(task).data, status=status.HTTP_200_OK)




 






class EditTaskView(generics.UpdateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    lookup_field = 'id'
    lookup_url_kwarg = 'task_id'  # Map the URL parameter 'task_id' to the 'id' field in the Task model

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        return Task.objects.filter(project__id=project_id, project__manager=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Store the old developer for comparison later
        old_developer = instance.developer

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Check if the developer has changed
        new_developer = instance.developer
        if old_developer != new_developer:
            # Send notification to the new developer
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'notifications_{new_developer.id}',
                {
                    'type': 'send_notification',
                    'notification': f'You have been assigned a new task: {instance.title}'
                }
            )

        return Response({
            'status': 'success',
            'message': 'Task updated successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

class DeleteTaskView(generics.DestroyAPIView):

    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    lookup_field = 'id'
    lookup_url_kwarg = 'task_id'

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        # Ensures that only tasks from the specified project managed by the current user are considered for deletion
        return Task.objects.filter(project__id=project_id, project__manager=self.request.user)

    def get_object(self):
        queryset = self.get_queryset()
        try:
            obj = queryset.get(id=self.kwargs[self.lookup_url_kwarg])
        except Task.DoesNotExist:
            raise NotFound(detail="Task not found.")
        return obj

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.project.manager != request.user:
            raise PermissionDenied(detail="You do not have permission to delete this task.")
        self.perform_destroy(instance)
        return Response({
            'status': 'success',
            'message': 'Task has been successfully deleted.'
        }, status=status.HTTP_200_OK)

#############risk_level########3
# views.py

class EvaluateRiskLevelView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def post(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)

        # Get the additional risk evaluation fields from the request payload
        project_category = request.data.get('project_category')
        requirement_category = request.data.get('requirement_category')
        risk_target_category = request.data.get('risk_target_category')
        probability = request.data.get('probability')
        magnitude_of_risk = request.data.get('magnitude_of_risk')
        impact = request.data.get('impact')
        dimension_of_risk = request.data.get('dimension_of_risk')
        affecting_no_of_modules = request.data.get('affecting_no_of_modules')
        fixing_duration_days = request.data.get('fixing_duration_days')
        fix_cost_percent = request.data.get('fix_cost_percent')
        priority = request.data.get('priority')

        # Ensure all necessary fields are provided
        required_fields = [
            project_category, requirement_category, risk_target_category, probability,
            magnitude_of_risk, impact, dimension_of_risk, affecting_no_of_modules,
            fixing_duration_days, fix_cost_percent, priority
        ]
        if any(field is None for field in required_fields):
            return Response({"error": "Missing required fields in the request payload."}, status=status.HTTP_400_BAD_REQUEST)

        # Use the edited requirements if available, otherwise use the original
        functional_requirements = project.edited_functional_requirements or project.functional_requirements
        non_functional_requirements = project.edited_non_functional_requirements or project.non_functional_requirements

        # Combine functional and non-functional requirements
        all_requirements = functional_requirements + non_functional_requirements

        # Prepare input data for the evaluate_risk_level function
        input_data = {
            "requirements": all_requirements,
            "project_category": project_category,
            "requirement_category": requirement_category,
            "risk_target_category": risk_target_category,
            "probability": probability,
            "magnitude_of_risk": magnitude_of_risk,
            "impact": impact,
            "dimension_of_risk": dimension_of_risk,
            "affecting_no_of_modules": affecting_no_of_modules,
            "fixing_duration_days": fixing_duration_days,
            "fix_cost_percent": fix_cost_percent,
            "priority": priority
        }

        # Evaluate risk level using the placeholder AI function
        risk_level = evaluate_risk_level(input_data)

        # Return the risk level as response
        return Response({"risk_level": risk_level}, status=status.HTTP_200_OK)








class TaskDetailForManagerView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def get(self, request, pk):
        try:
            task = Task.objects.get(pk=pk, project__manager=request.user)
        except Task.DoesNotExist:
            return Response({"detail": "Task not found or you do not have permission to view it."}, status=status.HTTP_404_NOT_FOUND)

        if task.status != 'completed':
            return Response({'message': 'Task is not yet completed.'}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure start_time and end_time are set
        if task.start_time is None or task.end_time is None:
            return Response({'message': 'Start time or end time is not set for this task.'}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate time taken by the developer
        actual_time_taken = task.end_time - task.start_time
        task.actual_time_spent = actual_time_taken
        task.save()

        # Ensure manager_end_time and manager_start_time are set
        if task.manager_start_time is None or task.manager_end_time is None:
            return Response({'message': 'Manager-assigned start time or end time is not set for this task.'}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate allocated time based on manager's assigned start and end times
        allocated_time = task.manager_end_time - task.manager_start_time

        if actual_time_taken < allocated_time:
            message = 'The task was completed earlier than the deadline.'
        elif actual_time_taken == allocated_time:
            message = 'The task was completed exactly on time.'
        else:
            message = 'The task was completed but exceeded the deadline.'

        # Format actual_time_taken into days, hours, minutes
        days = actual_time_taken.days
        seconds = actual_time_taken.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60

        actual_time_taken_str = f"{days} days, {hours} hours, {minutes} minutes"

        # Update developer KPIs
        developer_metrics, created = DeveloperMetrics.objects.get_or_create(developer=task.developer)
        developer_metrics.tasks_completed += 1

        if developer_metrics.average_completion_time:
            developer_metrics.average_completion_time = (
                developer_metrics.average_completion_time + actual_time_taken
            ) / 2
        else:
            developer_metrics.average_completion_time = actual_time_taken

        if developer_metrics.total_delivery_time and developer_metrics.total_allocated_time:
            developer_metrics.total_delivery_time += actual_time_taken
            developer_metrics.total_allocated_time += allocated_time
        else:
            developer_metrics.total_delivery_time = actual_time_taken
            developer_metrics.total_allocated_time = allocated_time

        developer_metrics.save()

        return Response({
            'task_name': task.title,
            'message': message,
            'time_taken': actual_time_taken_str,
            'allocated_time': str(allocated_time),
            'start_time': task.start_time,
            'end_time': task.end_time,
            'manager_start_time': task.manager_start_time,
            'manager_end_time': task.manager_end_time
        }, status=status.HTTP_200_OK)








class DeveloperMetricsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def get(self, request):
        # Get the projects managed by the authenticated manager
        projects_managed = Project.objects.filter(manager=request.user)
        
        # Get the developers assigned to these projects
        developers = CustomUser.objects.filter(assigned_tasks__project__in=projects_managed).distinct()
        
        metrics = []

        for developer in developers:
            tasks = Task.objects.filter(developer=developer, project__in=projects_managed)
            tasks_completed = tasks.filter(status='completed').count()

            developer_metrics = DeveloperMetrics.objects.get(developer=developer)
            tasks_reassigned = developer_metrics.tasks_reassigned
            
            if tasks_completed > 0:
                total_delivery_time = tasks.aggregate(
                    total_delivery_time=Sum(ExpressionWrapper(F('end_time') - F('start_time'), output_field=DurationField()))
                )['total_delivery_time']
                total_allocated_time = tasks.aggregate(
                    total_allocated_time=Sum(ExpressionWrapper(F('manager_end_time') - F('manager_start_time'), output_field=DurationField()))
                )['total_allocated_time']

                avg_delivery_time = total_delivery_time / tasks_completed if total_delivery_time else None
                avg_allocated_time = total_allocated_time / tasks_completed if total_allocated_time else None
                
                if avg_delivery_time and avg_allocated_time:
                    if avg_delivery_time < avg_allocated_time:
                        delivery_status = 'early'
                    elif avg_delivery_time == avg_allocated_time:
                        delivery_status = 'on time'
                    else:
                        delivery_status = 'late'
                else:
                    delivery_status = 'N/A'
                
                avg_completion_time = tasks.aggregate(
                    avg_completion_time=Avg(ExpressionWrapper(F('end_time') - F('start_time'), output_field=DurationField()))
                )['avg_completion_time']
                if avg_completion_time:
                    total_seconds = avg_completion_time.total_seconds()
                    hours = int(total_seconds // 3600)
                    minutes = int((total_seconds % 3600) // 60)
                    average_completion_time_str = f"{hours} hours, {minutes} minutes"
                else:
                    average_completion_time_str = "N/A"
            else:
                delivery_status = 'N/A'
                average_completion_time_str = "N/A"

            # Calculate the rating based on the metrics
            rating = self.calculate_rating(tasks_completed, tasks_reassigned, delivery_status)
            
            metrics.append({
                'developer': developer.username,
                'tasks_completed': tasks_completed,
                'average_completion_time': average_completion_time_str,
                'tasks_reassigned': tasks_reassigned,
                'average_delivery_status': delivery_status,
                'rating': rating,
            })

        return Response(metrics, status=status.HTTP_200_OK)

    def calculate_rating(self, tasks_completed, tasks_reassigned, delivery_status):
        # Define the rating criteria
        rating_criteria = {
            'tasks_completed': 0.3,
            'tasks_reassigned': 0.2,
            'delivery_status': 0.5,
        }

        # Calculate the rating
        rating = 0
        if tasks_completed > 0:
            rating += rating_criteria['tasks_completed']
        if tasks_reassigned == 0:
            rating += rating_criteria['tasks_reassigned']
        if delivery_status == 'early':
            rating += rating_criteria['delivery_status']
        elif delivery_status == 'on time':
            rating += rating_criteria['delivery_status'] * 0.8
        else:
            rating -= rating_criteria['delivery_status'] * 0.2

        # Normalize the rating to a scale of 1-5
        rating = round(rating * 5, 1)

        return rating


        
