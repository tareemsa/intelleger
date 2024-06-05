from rest_framework import generics, permissions,status
from manager.serializers import  TaskSerializer, ProjectSerializer
from manager.models import Task, Project
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.status import HTTP_200_OK
from .models import ToDo
from manager.models import DeveloperMetrics,Task
from .serializers import ToDoSerializer
from django.utils import timezone


#list alll developer tasks 

class DeveloperTaskListView(generics.ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(developers=self.request.user)
#list specific task details
class DeveloperTaskDetailView(generics.RetrieveAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(developers=self.request.user)
#list developer projects 
class DeveloperProjectListView(generics.ListAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(developers=self.request.user)
#list specific project details 
class DeveloperProjectDetailView(generics.RetrieveAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(developers=self.request.user)

#change_task_status
class StartTaskView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TaskSerializer
    def post(self, request, pk):
        task = Task.objects.get(pk=pk, developers=request.user)
        task.status = 'in_progress'
        task.start_time = timezone.now()  # Log start time
        task.save()
        return Response({'message': 'Task In Progress.'}, status=status.HTTP_200_OK)

class CompleteTaskView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        task = Task.objects.get(pk=pk, developers=request.user)
        if task.status == 'in_progress':
            task.status = 'completed'
            task.end_time = timezone.now()  # Log end time
            task.save()
            return Response({'message': 'Task completed.'}, status=status.HTTP_200_OK)
        return Response({'message': 'Task is not in progress.'}, status=status.HTTP_400_BAD_REQUEST)

#generate_code 
class GenerateCodeFromDescriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        description = request.data.get('description')
        # Placeholder for AI code generation
        generated_code = f"// Generated code for: {description}"
        return Response({'generated_code': generated_code}, status=HTTP_200_OK)


#to_do_list 
# todo_views.py


class ToDoListCreateView(generics.ListCreateAPIView):
    serializer_class = ToDoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ToDo.objects.filter(developer=self.request.user)

    def perform_create(self, serializer):
        serializer.save(developer=self.request.user)

class ToDoRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ToDo.objects.all()
    serializer_class = ToDoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ToDo.objects.filter(developer=self.request.user)

class RestartTaskView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            task = Task.objects.get(pk=pk, developer=request.user)
        except Task.DoesNotExist:
            return Response({'message': 'Task not found or you do not have permission to restart it.'}, status=status.HTTP_404_NOT_FOUND)

        if task.status == 'completed':
            task.status = 'in_progress'
            task.end_time = None  # Reset end time
            task.start_time = timezone.now()  # Log new start time
            task.save()

            # Update developer KPIs
            developer_metrics, created = DeveloperMetrics.objects.get_or_create(developer=task.developer)
            developer_metrics.tasks_reassigned += 1
            developer_metrics.save()

            return Response({'message': 'Task returned to In Progress.'}, status=status.HTTP_200_OK)

        return Response({'message': 'Task is not completed.'}, status=status.HTTP_400_BAD_REQUEST)
