from rest_framework import serializers
from .models import Project,Task
from .models import CustomUser
from django.utils import timezone

from rest_framework import serializers
from accounts.models import CustomUser
from .models import Project
from django.utils import timezone
from rest_framework.fields import DateTimeField

class ProjectSerializer(serializers.ModelSerializer):
    developers = serializers.SlugRelatedField(
        many=True,
        slug_field='email',
        queryset=CustomUser.objects.filter(admin_role=False)
    )
    
    deadline = DateTimeField(
        format='%Y-%m-%d', 
        input_formats=['%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']
    )

    class Meta:
        model = Project
        fields = ['id', 'name', 'scope', 'deadline', 'developers', 'created_at', 'updated_at']

    def create(self, validated_data):
        developer_emails = validated_data.pop('developers')
        developers = CustomUser.objects.filter(email__in=developer_emails, admin_role=False)
        
        validated_data['manager'] = self.context['request'].user
        project = super().create(validated_data)
        
        project.developers.set(developers)
        
        return project

    def validate_deadline(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("The deadline must be in the future.")
        return value

  

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username','email']  # Assuming username is used as the display name





from rest_framework import serializers
from rest_framework.fields import DateTimeField
from .models import Task, CustomUser, Project

class TaskSerializer(serializers.ModelSerializer):
    developer = serializers.SlugRelatedField(
        slug_field='email',
        queryset=CustomUser.objects.all(),
        many=False
    )

    datetime_field_params = {
        'format': '%Y-%m-%d',
        'input_formats': ['%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']
    }

    start_time = DateTimeField(**datetime_field_params)
    manager_start_time = DateTimeField(**datetime_field_params)
    manager_end_time = DateTimeField(**datetime_field_params)
    end_time = DateTimeField(**datetime_field_params)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'developer', 'status', 'project',
            'start_time', 'end_time', 'manager_start_time', 'manager_end_time'
        ]
        read_only_fields = ['project', 'start_time', 'end_time']

    def validate_developers(self, value):
        """
        Check that the developer is assigned to the project.
        """
        project_id = self.context['view'].kwargs.get('project_id')
        project = Project.objects.get(id=project_id)

        try:
            # Retrieve the developer object based on the email
            developer_email = value
            developer = CustomUser.objects.get(email=developer_email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError(f"Developer with email {developer_email} does not exist.")

        if developer not in project.developers.all():
            raise serializers.ValidationError(f"Developer {developer.email} is not assigned to this project.")

        return developer

    def validate_end_time(self, value):
        """
        Ensure that the task deadline is not before the project's deadline.
        """
        project_id = self.context['view'].kwargs.get('project_id')
        project = Project.objects.get(id=project_id)

        if value > project.manager_end_time:
            raise serializers.ValidationError("Task deadline cannot exceed the project's deadline.")
        return value




