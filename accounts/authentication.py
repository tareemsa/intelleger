from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            # Try to fetch the user by searching the email field
            user = UserModel.objects.get(Q(email__iexact=username))
            if user.check_password(password):
                return user
        except UserModel.DoesNotExist:
            # Return None if no user is found
            UserModel().set_password(password)  # This is done to mitigate timing attacks
        return None
