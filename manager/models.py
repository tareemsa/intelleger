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

    def __str__(self):
        return self.name

class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    developer = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='assigned_tasks')
    deadline = models.DateTimeField()
    status = models.CharField(max_length=50, default='pending')

    def __str__(self):
        return self.title

