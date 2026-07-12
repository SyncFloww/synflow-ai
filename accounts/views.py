from rest_framework import status
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)
from .services import (
    TokenService,
    UserService,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
)
from .serializers import (
    ProfileSerializer,
    ChangePasswordSerializer,
)

class RegisterAPIView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = RegisterSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        user = serializer.save()

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