from django.urls import path
from .views import UserRegistrationView, VerifyEmailView, UserDetailView,PasswordResetRequestView,UsernameUpdateView,PasswordUpdateView, PasswordResetView,LogoutView,CustomTokenObtainPairView,ResendVerificationCode
from rest_framework_simplejwt.views import  TokenRefreshView, TokenVerifyView

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('password-reset-request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/', PasswordResetView.as_view(), name='password-reset'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),#login
    path('resend-verification/', ResendVerificationCode.as_view(), name='resend-verification'),
    path('user/update-username/', UsernameUpdateView.as_view(), name='update-username'),
    path('user/update-password/', PasswordUpdateView.as_view(), name='update-password'),
    path('user/details/', UserDetailView.as_view(), name='user-detail'),
 
]
