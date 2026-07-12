from rest_framework_simplejwt.tokens import RefreshToken


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