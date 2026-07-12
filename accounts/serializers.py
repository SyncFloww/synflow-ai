from django.contrib.auth import authenticate
from django.db import transaction
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .utils import generate_referral_code
from .validators import validate_password_strength


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "referral_code",
            "is_verified",
            "date_joined",
        )
        read_only_fields = (
            "id",
            "referral_code",
            "is_verified",
            "date_joined",
        )


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )

    confirm_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    referral_code = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "password",
            "confirm_password",
            "referral_code",
        )

    def validate_email(self, value):
        value = value.lower()

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )

        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {
                    "confirm_password": "Passwords do not match."
                }
            )

        validate_password_strength(attrs["password"])

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        referral = validated_data.pop("referral_code", "").strip()
        validated_data.pop("confirm_password")

        referred_by = None

        if referral:
            try:
                referred_by = User.objects.get(
                    referral_code=referral
                )
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    {
                        "referral_code": "Invalid referral code."
                    }
                )

        user = User.objects.create_user(
            email=validated_data["email"].lower(),
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            referred_by=referred_by,
        )

        while True:
            code = generate_referral_code()

            if not User.objects.filter(
                referral_code=code
            ).exists():
                user.referral_code = code
                break

        user.save(update_fields=["referral_code"])

        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()

    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    remember_me = serializers.BooleanField(
        default=False,
        required=False,
    )

    def validate(self, attrs):
        email = attrs.get("email").lower()
        password = attrs.get("password")

        user = authenticate(
            username=email,
            password=password,
        )

        if user is None:
            raise serializers.ValidationError(
                {
                    "detail": "Invalid email or password."
                }
            )

        if not user.is_active:
            raise serializers.ValidationError(
                {
                    "detail": "This account has been disabled."
                }
            )

        attrs["user"] = user

        return attrs

    @staticmethod
    def get_tokens(user):
        refresh = RefreshToken.for_user(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
        
        
class ProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "referral_code",
            "is_verified",
            "date_joined",
        )
        read_only_fields = (
            "email",
            "referral_code",
            "is_verified",
            "date_joined",
        )
        

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    new_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    confirm_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        user = self.context["request"].user

        if not user.check_password(attrs["old_password"]):
            raise serializers.ValidationError({
                "old_password": "Old password is incorrect."
            })

        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match."
            })

        validate_password(attrs["new_password"])

        return attrs