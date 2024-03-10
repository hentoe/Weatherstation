from rest_framework.authentication import TokenAuthentication


class APIKeyAuthentication(TokenAuthentication):
    def authenticate(self, request):
        # Custom logic to check for a different header or token parameter
        token = request.META.get('HTTP_X_API_KEY')
        if not token:
            return None

        return self.authenticate_credentials(token)
