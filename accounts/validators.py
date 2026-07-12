import re

from django.core.exceptions import ValidationError


def validate_password_strength(password):

    if len(password) < 8:
        raise ValidationError(
            "Password must contain at least 8 characters."
        )

    if not re.search(r"[A-Z]", password):
        raise ValidationError(
            "Password must contain an uppercase letter."
        )

    if not re.search(r"[a-z]", password):
        raise ValidationError(
            "Password must contain a lowercase letter."
        )

    if not re.search(r"\d", password):
        raise ValidationError(
            "Password must contain a number."
        )