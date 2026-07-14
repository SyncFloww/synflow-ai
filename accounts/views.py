from rest_framework import status
from django.conf import settings
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)
from .services import (
    TokenService,
    UserService,
    GoogleAuthService,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    ReferralStatsSerializer,
    GoogleLoginSerializer
)
from .serializers import (
    ProfileSerializer,
    ChangePasswordSerializer,
)
from .models import User
from .models import EmailVerification, PasswordReset
from .serializers import TokenSerializer, PasswordResetConfirmSerializer
from django.contrib.auth.password_validation import validate_password
from django.db import transaction

class RegisterAPIView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = RegisterSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        EmailVerification.issue(user)

        tokens = TokenService.create_tokens(user)

        return Response(
            {
                "success": True,
                "message": "Account created successfully.",
                "user": UserSerializer(user).data,
                "tokens": tokens,
            },
            status=status.HTTP_201_CREATED,
        )
        
        
class LoginAPIView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = LoginSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        tokens = TokenService.create_tokens(user)

        return Response(
            {
                "success": True,
                "message": "Login successful.",
                "user": UserSerializer(user).data,
                "tokens": tokens,
            }
        )
        
        
class CurrentUserAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        serializer = UserSerializer(request.user)

        return Response(serializer.data)
    

class LogoutAPIView(APIView):
    # Allow any so logout works even when the access token has expired
    permission_classes = [AllowAny]

    def post(self, request):

        refresh_token = request.data.get("refresh")

        if not refresh_token:
            # No refresh token provided — just treat as already logged out
            return Response(
                {
                    "success": True,
                    "message": "Logged out successfully."
                }
            )

        try:

            TokenService.blacklist_token(
                refresh_token
            )

            return Response(
                {
                    "success": True,
                    "message": "Logged out successfully."
                }
            )

        except Exception:
            # Even if blacklisting fails, treat as logged out client-side
            return Response(
                {
                    "success": True,
                    "message": "Logged out successfully."
                }
            )
            
            

class ProfileAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        serializer = ProfileSerializer(request.user)

        return Response(serializer.data)

    def put(self, request):

        serializer = ProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response({
            "success": True,
            "message": "Profile updated successfully.",
            "user": serializer.data,
        })
        

class ChangePasswordAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)

        UserService.change_password(
            request.user,
            serializer.validated_data["new_password"],
        )

        return Response({
            "success": True,
            "message": "Password updated successfully."
        })


class ReferralStatsAPIView(APIView):
    """Return the authenticated user's referral stats and dashboard data."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ReferralStatsSerializer(
            request.user,
            context={"request": request},
        )
        return Response({
            "success": True,
            "data": serializer.data,
        })


class ValidateReferralCodeAPIView(APIView):
    """Validate a referral code without requiring authentication.
    Used during signup so the frontend can give instant feedback.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        code = request.query_params.get("code", "").strip()

        if not code:
            return Response(
                {"valid": False, "detail": "No code provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            referrer = User.objects.get(referral_code=code)
            return Response({
                "valid": True,
                "referrer_name": referrer.first_name or referrer.email.split("@")[0],
            })
        except User.DoesNotExist:
            return Response(
                {"valid": False, "detail": "Invalid referral code."},
                status=status.HTTP_404_NOT_FOUND,
            )


class GoogleLoginAPIView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):
        if not settings.GOOGLE_OAUTH2_CLIENT_ID:
            return Response(
                {"success": False, "message": "Google sign-in is not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = GoogleAuthService.authenticate(
                serializer.validated_data["token"]
            )

        except ValueError as e:
            return Response(
                {
                    "success": False,
                    "message": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        tokens = TokenService.create_tokens(user)

        return Response(
            {
                "success": True,
                "message": "Google login successful.",
                "user": UserSerializer(user).data,
                "tokens": tokens,
            }
        )


class VerifyEmailAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        verification = EmailVerification.consume(serializer.validated_data["token"])
        if not verification:
            return Response({"detail": "This verification link is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)
        verification.user.is_verified = True
        verification.user.save(update_fields=["is_verified"])
        return Response({"success": True, "message": "Email verified successfully."})


class PasswordResetRequestAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        if email:
            user = User.objects.filter(email=email, is_active=True).first()
            if user:
                PasswordReset.issue(user)
        # Do not disclose whether an account exists.
        return Response({"success": True, "message": "If that email exists, a reset link has been sent."})


class PasswordResetConfirmAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reset = PasswordReset.consume(serializer.validated_data["token"])
        if not reset:
            return Response({"detail": "This reset link is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)
        reset.user.set_password(serializer.validated_data["new_password"])
        reset.user.save(update_fields=["password"])
        return Response({"success": True, "message": "Password reset successfully."})


class DeleteAccountAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        password = request.data.get("password")
        if not password or not request.user.check_password(password):
            return Response({"password": ["Your password is required to delete the account."]}, status=status.HTTP_400_BAD_REQUEST)
        request.user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
