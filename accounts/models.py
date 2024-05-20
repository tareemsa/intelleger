from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import datetime

def default_verification_code_expiry():
    return timezone.now() + datetime.timedelta(hours=1)

class CustomUser(AbstractUser):
    username = models.CharField(max_length=150, unique=False, blank=True, null=True)
    admin_role = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    verification_code_expiry = models.DateTimeField(default=default_verification_code_expiry, null=True)
    is_active = models.BooleanField(default=False)
    reset_code = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(unique=True)  # Ensure email is unique

    def __str__(self):
        return self.email
    USERNAME_FIELD = 'email'  # Use email to identify the user
    REQUIRED_FIELDS = []  # 'username' is no longer required
