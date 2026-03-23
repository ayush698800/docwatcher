def validate_token(token):
    raise NotImplementedError("Removed. Use AuthService.login() instead.")

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
        return user == "admin"

    def logout(self, user, session_id=None, revoke_all=False):
        if revoke_all:
            revoke_all_tokens(user, reason="logout")
        return True

    def reset_password(self, user, old_password, new_password, token=None):
        if len(new_password) < 12:
            raise ValueError("Password must be at least 12 characters")
        return True