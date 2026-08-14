import base64
import json
import time
import secrets
import logging
from typing import Dict, Any, Tuple, Optional
from django.conf import settings
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Derive a 32-byte Fernet key from Django SECRET_KEY
def _get_fernet():
    try:
        from cryptography.fernet import Fernet
        import hashlib
        key_raw = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        key_b64 = base64.urlsafe_b64encode(key_raw)
        return Fernet(key_b64)
    except Exception as e:
        logger.error(f"Fernet initialization error: {e}")
        return None

class TokenEncryptionService:
    """
    Symmetric AES-256 (Fernet) token encryption service.
    Protects OAuth Access and Refresh Tokens before storing in DB.
    """
    @staticmethod
    def encrypt(token: str) -> str:
        if not token:
            return ""
        fernet = _get_fernet()
        if not fernet:
            return token  # Fallback if cryptography module uninitialized
        try:
            return fernet.encrypt(token.encode('utf-8')).decode('utf-8')
        except Exception as e:
            logger.error(f"Token encryption failed: {e}")
            return token

    @staticmethod
    def decrypt(encrypted_token: str) -> str:
        if not encrypted_token:
            return ""
        fernet = _get_fernet()
        if not fernet:
            return encrypted_token
        try:
            return fernet.decrypt(encrypted_token.encode('utf-8')).decode('utf-8')
        except Exception as e:
            # If token is unencrypted legacy string or decryption fails
            logger.warning(f"Token decryption fallback: {e}")
            return encrypted_token

class OAuthStateManager:
    """
    Cryptographically signed, single-use OAuth State token manager.
    Prevents CSRF, state replay, cross-tenant/cross-brand injection attacks.
    """
    SIGNER_SALT = "syncfloww.social.oauth.state"
    MAX_AGE_SECONDS = 900  # 15 minutes expiration

    @classmethod
    def generate_state(
        cls,
        user_id: int,
        workspace_id: int,
        brand_id: int,
        provider: str,
        code_verifier: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Generates HMAC-signed state token binding user, workspace, brand, provider, and PKCE verifier.
        Returns: (signed_state_string, code_verifier)
        """
        nonce = secrets.token_hex(16)
        payload = {
            "u": user_id,
            "w": workspace_id,
            "b": brand_id,
            "p": provider.lower(),
            "n": nonce,
            "t": int(time.time()),
            "cv": code_verifier or ""
        }

        # Store PKCE verifier in cache keyed by nonce if present
        if code_verifier:
            cache.set(f"oauth_pkce:{nonce}", code_verifier, timeout=cls.MAX_AGE_SECONDS)

        raw_json = json.dumps(payload)
        signer = TimestampSigner(salt=cls.SIGNER_SALT)
        signed_state = signer.sign(raw_json)
        return signed_state, code_verifier or ""

    @classmethod
    def validate_and_consume_state(cls, state_str: str, expected_provider: str) -> Dict[str, Any]:
        """
        Validates HMAC signature, expiration (15 mins), single-use nonce, and expected provider.
        Returns extracted state payload or raises ValueError.
        """
        if not state_str:
            raise ValueError("State parameter is missing.")

        signer = TimestampSigner(salt=cls.SIGNER_SALT)
        try:
            raw_json = signer.unsign(state_str, max_age=cls.MAX_AGE_SECONDS)
            payload = json.loads(raw_json)
        except SignatureExpired:
            raise ValueError("OAuth state has expired. Please initiate connection again.")
        except BadSignature:
            raise ValueError("Invalid or tampered OAuth state parameter.")
        except Exception as e:
            raise ValueError(f"State validation error: {str(e)}")

        nonce = payload.get("n")
        if not nonce:
            raise ValueError("Malformed state payload.")

        # Single-use nonce enforcement via cache
        cache_key = f"oauth_nonce_used:{nonce}"
        if cache.get(cache_key):
            raise ValueError("OAuth state has already been used (replay attack prevented).")

        # Mark nonce as consumed for 30 minutes
        cache.set(cache_key, True, timeout=1800)

        # Check provider match
        provider = payload.get("p", "").lower()
        if provider != expected_provider.lower():
            raise ValueError(f"State provider mismatch. Expected '{expected_provider}', got '{provider}'.")

        # Retrieve PKCE code verifier if cached
        pkce_verifier = payload.get("cv") or cache.get(f"oauth_pkce:{nonce}") or ""

        return {
            "user_id": payload.get("u"),
            "workspace_id": payload.get("w"),
            "brand_id": payload.get("b"),
            "provider": provider,
            "nonce": nonce,
            "code_verifier": pkce_verifier
        }
