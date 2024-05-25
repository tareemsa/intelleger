from django.db import models
from django.utils import timezone
from accounts.models import CustomUser
from django.conf import settings


class Project(models.Model):
    name = models.CharField(max_length=200)
    scope = models.TextField()
    deadline = models.DateTimeField(default=timezone.now)
    developers = models.ManyToManyField('accounts.CustomUser', related_name='assigned_projects')
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ai_requirements = models.JSONField(default=dict, blank=True)
    slack_channel_id = models.CharField(max_length=100, blank=True, null=True)
    def __str__(self):
        return self.name

class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    developers = models.ManyToManyField(CustomUser, related_name='assigned_tasks')
    deadline = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, default='pending')
    
    def __str__(self):
        return self.title

