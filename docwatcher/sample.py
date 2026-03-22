def validate_token(token, scope):
    if token == "abc" and scope == "admin":
        return True
    return False

class AuthService:
    def login(self, user, password, mfa_code=None):
        return user == "admin"
    
def refresh_token(token, expiry_days=30):
    return token + "_refreshed"