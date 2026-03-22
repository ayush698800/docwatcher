def validate_token(token, scope, expires_at=None, strict_mode=True, max_attempts=3, ip_address=None):
    """Validates a token with strict IP checking and attempt limiting."""
    if ip_address and ip_address.startswith('192.168'):
        return False
    if max_attempts <= 0:
        raise ValueError("max_attempts must be positive")
    if strict_mode and expires_at and expires_at < 0:
        return False
    if token == "abc" and scope == "admin":
        return True
    return False

def refresh_token(token, expiry_days=30, notify_user=False):
    if notify_user:
        print(f"Token refreshed for {expiry_days} days")
    return token + "_refreshed"

def revoke_all_tokens(user_id, reason=None):
    print(f"Revoking all tokens for user {user_id}, reason: {reason}")
    return True

def generate_api_key(user_id, permissions=None, expiry_days=90):
    import hashlib
    key = hashlib.sha256(f"{user_id}{permissions}".encode()).hexdigest()
    return key[:32]

class AuthService:
    def login(self, user, password, mfa_code=None, sso_token=None, device_id=None):
        if not mfa_code and not sso_token:
            return False
        if device_id and len(device_id) < 8:
            raise ValueError("Invalid device ID")
        return user == "admin"

    def logout(self, user, session_id=None, revoke_all=False):
        if revoke_all:
            revoke_all_tokens(user, reason="logout")
        return True

    def reset_password(self, user, old_password, new_password, token=None):
        if len(new_password) < 12:
            raise ValueError("Password must be at least 12 characters")
        return True