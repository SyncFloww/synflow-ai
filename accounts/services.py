from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.db import IntegrityError, transaction
from google.auth.transport import requests
from google.oauth2 import id_token
import requests as http_requests

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
        if not email or not payload.get("email_verified"):
            raise ValueError("Google token does not contain a verified email.")
            
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


class FacebookAuthService:
    """Validate a Facebook user token server-side before creating a session."""

    GRAPH_URL = "https://graph.facebook.com/v23.0"
    REQUEST_TIMEOUT_SECONDS = 10

    @classmethod
    def _get_json(cls, url, *, params, error_message):
        try:
            response = http_requests.get(
                url,
                params=params,
                timeout=cls.REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            return response.json()
        except (http_requests.RequestException, ValueError) as exc:
            raise ValueError(error_message) from exc

    @classmethod
    def authenticate(cls, access_token):
        if not settings.FACEBOOK_APP_ID or not settings.FACEBOOK_APP_SECRET:
            raise ValueError("Facebook sign-in is not configured.")

        app_token = f"{settings.FACEBOOK_APP_ID}|{settings.FACEBOOK_APP_SECRET}"
        debug_data = cls._get_json(
            f"{cls.GRAPH_URL}/debug_token",
            params={"input_token": access_token, "access_token": app_token},
            error_message="Could not verify the Facebook sign-in token.",
        )
        token_data = debug_data.get("data", {}) if isinstance(debug_data, dict) else {}

        if (
            not isinstance(token_data, dict)
            or not token_data.get("is_valid")
            or str(token_data.get("app_id")) != str(settings.FACEBOOK_APP_ID)
        ):
            raise ValueError("Invalid Facebook sign-in token.")

        profile_data = cls._get_json(
            f"{cls.GRAPH_URL}/me",
            params={"fields": "id,email,first_name,last_name", "access_token": access_token},
            error_message="Could not retrieve the Facebook profile.",
        )

        # The Graph profile must belong to the token that was validated above.
        # This is normally guaranteed by /me, but keeping the explicit check
        # prevents an unexpected API response from being used to sign in.
        if not isinstance(profile_data, dict) or str(profile_data.get("id")) != str(token_data.get("user_id")):
            raise ValueError("Invalid Facebook sign-in token.")

        email = profile_data.get("email")
        if not email:
            raise ValueError("Facebook did not provide an email address. Please grant email access or use another sign-in method.")

        from .models import User
        from .utils import generate_referral_code

        normalized_email = email.lower()
        user = User.objects.filter(email=normalized_email).first()
        if user is None:
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        email=normalized_email,
                        password=None,
                        first_name=profile_data.get("first_name", ""),
                        last_name=profile_data.get("last_name", ""),
                        is_verified=True,
                    )

                    while True:
                        code = generate_referral_code()
                        if not User.objects.filter(referral_code=code).exists():
                            user.referral_code = code
                            break
                    user.save(update_fields=["referral_code"])
            except IntegrityError:
                # A parallel sign-in may have created the same email first.
                user = User.objects.get(email=normalized_email)
        elif not user.is_active:
            raise ValueError("This account has been disabled.")
        else:
            user.first_name = user.first_name or profile_data.get("first_name", "")
            user.last_name = user.last_name or profile_data.get("last_name", "")
            user.is_verified = True
            user.save(update_fields=["first_name", "last_name", "is_verified"])

        if not user.is_active:
            raise ValueError("This account has been disabled.")

        if not user.referral_code:
            while True:
                code = generate_referral_code()
                if not User.objects.filter(referral_code=code).exists():
                    user.referral_code = code
                    break
            user.save(update_fields=["referral_code"])

        return user
