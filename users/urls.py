from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, LoginView, MeView, LogoutView, PasswordResetView,
    PasswordResetConfirmView, VerifyEmailView, ResendVerificationView,
    ChangePasswordView, GoogleAuthView, DeleteAccountView, PersonalSpaceView
)

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/me/', MeView.as_view(), name='me'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/password-reset/', PasswordResetView.as_view(), name='password_reset'),
    path('auth/password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('auth/verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('auth/resend-verification/', ResendVerificationView.as_view(), name='resend_verification'),
    path('auth/google/', GoogleAuthView.as_view(), name='google_auth'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('auth/delete-account/', DeleteAccountView.as_view(), name='delete_account'),
    path('me/', MeView.as_view(), name='me_direct'),
    path('me/personal-space/', PersonalSpaceView.as_view(), name='personal_space'),
    path('personal-space/', PersonalSpaceView.as_view(), name='personal_space_direct'),
]

