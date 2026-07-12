import random
import string


def generate_referral_code(length=8):
    """
    Generate a unique referral code.
    Example: GRT7KQ92
    """
    prefix = "GRT"

    characters = string.ascii_uppercase + string.digits

    return prefix + "".join(
        random.choices(characters, k=length)
    )