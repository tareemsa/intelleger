from django.db import models
from django.utils import timezone

class Project(models.Model):
    name = models.CharField(max_length=200)
    scope = models.TextField()
    deadline = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
