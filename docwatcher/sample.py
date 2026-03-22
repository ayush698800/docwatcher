def validate_token(token):
    if token == "abc":
        return True
    return False

class AuthService:
    def login(self, user, password):
        return user == "admin"