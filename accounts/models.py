from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import datetime

def default_verification_code_expiry():
    return timezone.now() + datetime.timedelta(hours=1)

class CustomUser(AbstractUser):
    admin_role = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    verification_code_expiry = models.DateTimeField(default=default_verification_code_expiry, null=True)
    is_active = models.BooleanField(default=False)
    reset_code = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.username
