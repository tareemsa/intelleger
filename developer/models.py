from django.db import models

from accounts.models import CustomUser


class ToDo(models.Model):
    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    developer = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

