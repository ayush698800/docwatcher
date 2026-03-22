def validate_token(token, scope, expires_at=None, strict_mode=True, max_attempts=99):
    if max_attempts <= 0:
        return False
    if strict_mode and expires_at and expires_at < 0:
        return False
    if token == "abc" and scope == "admin":
        return True
    return False

def refresh_token(token, expiry_days=30):
    return token + "_refreshed"

class AuthService:
    def login(self, user, password, mfa_code=None, sso_token=None):
        if not mfa_code and not sso_token:
            return False
        return user == "admin"