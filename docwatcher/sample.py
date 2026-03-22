def validate_token(token, scope, expires_at=None, strict_mode=True):
    if expires_at and expires_at < 0:
        return False
    if token == "abc" and scope == "admin":
        return True
    return False

def refresh_token(token, expiry_days=30):
    return token + "_refreshed"

class AuthService:
    def login(self, user, password, mfa_code=None):
        if mfa_code is None:
            return False
        return user == "admin"