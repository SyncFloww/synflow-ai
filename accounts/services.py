from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from google.auth.transport import requests
from google.oauth2 import id_token

class TokenService:
    @staticmethod
    def create_tokens(user):
        refresh = RefreshToken.for_user(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

    @staticmethod
    def blacklist_token(refresh_token):
        token = RefreshToken(refresh_token)
        token.blacklist()
        
        
class UserService:

    @staticmethod
    def change_password(user, password):

        user.set_password(password)

        user.save(update_fields=["password"])

        return user
    

class GoogleAuthService:

    @staticmethod
    def verify_google_token(token):
        """
        Verify a Google ID token and return the decoded payload.
        """
        try:
            payload = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                settings.GOOGLE_OAUTH2_CLIENT_ID,
            )

            return payload

        except ValueError:
            return None

    @classmethod
    def authenticate(cls, token):
        payload = cls.verify_google_token(token)
        if not payload:
            raise ValueError("Invalid Google token.")
            
        email = payload.get("email")
        if not email:
            raise ValueError("Google token does not contain an email.")
            
        email = email.lower()
        given_name = payload.get("given_name", "")
        family_name = payload.get("family_name", "")
        
        from .models import User
        user = User.objects.filter(email=email).first()
        if not user:
            user = User.objects.create_user(
                email=email,
                first_name=given_name,
                last_name=family_name,
                is_verified=True,
            )
            # generate referral code
            from .utils import generate_referral_code
            while True:
                code = generate_referral_code()
                if not User.objects.filter(referral_code=code).exists():
                    user.referral_code = code
                    break
            user.save()
        else:
            if not user.first_name:
                user.first_name = given_name
            if not user.last_name:
                user.last_name = family_name
            user.is_verified = True
            user.save()
            
        return user