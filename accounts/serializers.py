
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import datetime
from django.contrib.auth import get_user_model, authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import secrets
from rest_framework_simplejwt.exceptions import AuthenticationFailed

User = get_user_model()

def send_verification_email(user):
    subject = 'Verify your account'
    message = f'Your verification code is: {user.verification_code}'
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )




class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    admin_role = serializers.BooleanField(required=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'password', 'password2', 'email', 'admin_role']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords must match"})
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "This email is already registered."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User(
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data['email'],
            admin_role=validated_data.get('admin_role', False),
            is_active=False  # User should not be active until their email is verified
        )
        user.set_password(validated_data['password'])
        user.verification_code = secrets.token_urlsafe(16)[:6]
        user.verification_code_expiry = timezone.now() + datetime.timedelta(minutes=10)
        try:
            user.save()
            send_verification_email(user)
            return user
        except Exception as e:
            raise serializers.ValidationError({"email": "Failed to send verification email, please try again."})


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email address.")
        return value

    def save(self):
        user = User.objects.get(email=self.validated_data['email'])
        user.reset_code = secrets.token_urlsafe(10)
        user.save()
        send_mail(
            'Password Reset Request',
            f'Your password reset code is: {user.reset_code}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )



class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    reset_code = serializers.CharField(max_length=100)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate(self, data):
        if not User.objects.filter(email=data['email'], reset_code=data['reset_code']).exists():
            raise serializers.ValidationError("Invalid reset code or email.")
        return data

    def save(self):
        user = User.objects.get(email=self.validated_data['email'])
        user.set_password(self.validated_data['new_password'])
        user.reset_code = None  # Clear the reset code after successful password change
        user.save()





class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.EMAIL_FIELD

    def validate(self, attrs):
        # Replace 'username' with 'email' which should be defined in your user model
        email = attrs.get('email')
        password = attrs.get('password')

        # Use Django's authentication framework to attempt to authenticate the user
        user = authenticate(username=email, password=password)  # Ensure your auth backend matches this call

        # Specific error handling for failed authentication
        if not user:
            raise AuthenticationFailed('No active account found with the given credentials', 'no_active_account')

        # Check for the active status of the account
        if not user.is_active:
            raise AuthenticationFailed('This account is inactive.', 'account_inactive')

        # Everything is fine, proceed with token creation
        refresh = self.get_token(user)

        # Prepare and return the response data
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'email': user.email
        }





