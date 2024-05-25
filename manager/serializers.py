from rest_framework import serializers
from .models import Project,Task
from .models import CustomUser
from django.utils import timezone

class ProjectSerializer(serializers.ModelSerializer):
    developers = serializers.PrimaryKeyRelatedField(many=True, queryset=CustomUser.objects.filter(admin_role=False))
    class Meta:
        model = Project
        fields = ['id', 'name', 'scope', 'deadline', 'developers','created_at', 'updated_at']

    def create(self, validated_data):
        # Assuming `self.context['request'].user` is the logged-in user
        validated_data['manager'] = self.context['request'].user
        return super().create(validated_data) 
    def validate_deadline(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("The deadline must be in the future.")
        return value   

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username','email']  # Assuming username is used as the display name



from rest_framework import serializers

class TaskSerializer(serializers.ModelSerializer):
    developers = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), many=True)

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'developers', 'deadline', 'status', 'project']
        read_only_fields = ['project']

    def validate_developers(self, value):
        """
        Check that each developer is assigned to the project.
        """
        project_id = self.context['view'].kwargs.get('project_id')
        project = Project.objects.get(id=project_id)

        for developer in value:
            if developer not in project.developers.all():
                raise serializers.ValidationError(f"Developer {developer} is not assigned to this project.")
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



