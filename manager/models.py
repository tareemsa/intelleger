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
    functional_requirements = models.JSONField(default=list)
    non_functional_requirements = models.JSONField(default=list)
    edited_functional_requirements = models.JSONField(default=list, blank=True, null=True)
    edited_non_functional_requirements = models.JSONField(default=list, blank=True, null=True)
    def __str__(self):
        return self.name



class Task(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    developers = models.ManyToManyField(CustomUser, related_name='assigned_tasks')
    #deadline = models.DateTimeField(null=True, blank=True)
    manager_end_time=models.DateTimeField(null=True, blank=True)
    manager_start_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, default='not_started', choices=STATUS_CHOICES)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if self.status == 'in_progress' and self.start_time is None:
            self.start_time = timezone.now()
        if self.status == 'completed' and self.end_time is None:
            self.end_time = timezone.now()
        super(Task, self).save(*args, **kwargs)

    def __str__(self):
        return self.title


