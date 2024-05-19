from rest_framework import serializers
from .models import Project,Task
from .models import CustomUser

class ProjectSerializer(serializers.ModelSerializer):
    developers = serializers.PrimaryKeyRelatedField(many=True, queryset=CustomUser.objects.filter(admin_role=False))
    class Meta:
        model = Project
        fields = ['id', 'name', 'scope', 'deadline', 'developers','created_at', 'updated_at']

    def create(self, validated_data):
        # Assuming `self.context['request'].user` is the logged-in user
        validated_data['manager'] = self.context['request'].user
        return super().create(validated_data)    

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username','email']  # Assuming username is used as the display name

   

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username','email']  # Assuming username is used as the display name



class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'developer', 'deadline', 'status', 'project']
        read_only_fields = ['project']  # Project will be assigned in the view, not through the serializer directly

    def validate_developer(self, value):
        """
        Check that the developer is assigned to the project.
        """
        project_id = self.context['view'].kwargs.get('project_id')
        project = Project.objects.get(id=project_id)

        if value not in project.developers.all():
            raise serializers.ValidationError("Developer is not assigned to this project.")
        return value

    def validate_deadline(self, value):
        """
        Ensure that the task deadline is not before the project's deadline.
        """
        project_id = self.context['view'].kwargs.get('project_id')
        project = Project.objects.get(id=project_id)

        if value > project.deadline:
            raise serializers.ValidationError("Task deadline cannot exceed the project's deadline.")
        return value

class TaskAssignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['developer']

class UpdateDevelopersSerializer(serializers.ModelSerializer):
    developers = serializers.PrimaryKeyRelatedField(many=True, queryset=CustomUser.objects.filter(admin_role=False))

    class Meta:
        model = Project
        fields = ['developers'] 