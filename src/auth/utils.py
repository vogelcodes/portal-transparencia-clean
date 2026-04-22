"""
Security Utilities - Salt, Pepper, and Hash
"""
import bcrypt
import hashlib
import secrets
import hmac
import jwt
from datetime import datetime, timezone


def generate_salt() -> str:
    """Generate a cryptographically secure random salt."""
    return secrets.token_hex(16)


def hash_password(password: str, salt: str) -> str:
    """Hash password using bcrypt with a per-user salt."""
    password_with_salt = f"{password}{salt}".encode('utf-8')
    hashed = bcrypt.hashpw(password_with_salt, bcrypt.gensalt(rounds=12))
    return hashed.decode('utf-8')


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    """Verify a password against stored hash."""
    try:
        password_with_salt = f"{password}{salt}".encode('utf-8')
        stored_hash = password_hash.encode('utf-8')
        return bcrypt.checkpw(password_with_salt, stored_hash)
    except Exception:
        return False


def generate_token() -> str:
    """Generate a secure random token for sessions"""
    return secrets.token_urlsafe(64)


def generate_api_key() -> str:
    """Generate a secure API key"""
    return f"ptk_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(api_key: str, api_key_hash: str) -> bool:
    """Verify an API key against stored hash (timing-safe)."""
    return hmac.compare_digest(hash_api_key(api_key), api_key_hash)


def hash_session_token(token: str) -> str:
    """Hash a JWT before persisting/looking-up in DB. Prevents raw token
    exposure if the DB is compromised."""
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password meets security requirements."""
    if len(password) < 8:
        return False, "A senha deve ter pelo menos 8 caracteres"
    if not any(c.isupper() for c in password):
        return False, "A senha deve conter pelo menos 1 letra maiúscula"
    if not any(c.islower() for c in password):
        return False, "A senha deve conter pelo menos 1 letra minúscula"
    if not any(c.isdigit() for c in password):
        return False, "A senha deve conter pelo menos 1 número"
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        return False, "A senha deve conter pelo menos 1 caractere especial (!@#$%)"
    return True, ""


def sanitize_username(username: str) -> str:
    """Sanitize username to prevent injection"""
    return ''.join(c for c in username if c.isalnum() or c in '_-').lower()


def sanitize_email(email: str) -> str:
    """Basic email sanitization"""
    return email.strip().lower()


_LOGIN_MAX_ATTEMPTS = 5
_LOGIN_LOCKOUT_SECONDS = 300


def _login_key(identifier: str) -> str:
    return f"login:attempts:{identifier}"


def _lockout_key(identifier: str) -> str:
    return f"login:lockout:{identifier}"


def is_login_locked(identifier: str) -> bool:
    from src.rate_limit import get_redis
    return get_redis().exists(_lockout_key(identifier)) == 1


def record_login_attempt(identifier: str) -> None:
    from src.rate_limit import get_redis
    r = get_redis()
    key = _login_key(identifier)
    pipe = r.pipeline()
    pipe.incr(key)
    pipe.expire(key, _LOGIN_LOCKOUT_SECONDS)
    count, _ = pipe.execute()
    if int(count) >= _LOGIN_MAX_ATTEMPTS:
        r.setex(_lockout_key(identifier), _LOGIN_LOCKOUT_SECONDS, 1)


def clear_login_attempts(identifier: str) -> None:
    from src.rate_limit import get_redis
    r = get_redis()
    r.delete(_login_key(identifier), _lockout_key(identifier))


def get_remaining_lockout(identifier: str) -> int:
    from src.rate_limit import get_redis
    ttl = get_redis().ttl(_lockout_key(identifier))
    return max(0, int(ttl)) if ttl and ttl > 0 else 0


def generate_jwt(user_id: int, expires_at: datetime, secret_key: str) -> str:
    payload = {
        'user_id': user_id,
        'exp': expires_at,
        'iat': datetime.now(timezone.utc),
        'jti': secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, secret_key, algorithm='HS256')


def verify_jwt(token: str, secret_key: str):
    try:
        return jwt.decode(token, secret_key, algorithms=['HS256'])
    except Exception:
        return None
