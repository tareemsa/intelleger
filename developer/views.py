from rest_framework import generics, permissions
from manager.serializers import  TaskSerializer, ProjectSerializer
from manager.models import Task, Project
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.status import HTTP_200_OK
from .models import ToDo
from .serializers import ToDoSerializer



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
    def post(self, request, pk):
        task = Task.objects.get(pk=pk)
        task.status = 'in_progress'
        task.save()
        return Response({'task In_Progress.'},status=HTTP_200_OK)

class CompleteTaskView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, pk):
        task = Task.objects.get(pk=pk)
        task.status = 'done'
        task.save()
        return Response({'message': 'task completed '},status=HTTP_200_OK)

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

