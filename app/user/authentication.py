from rest_framework.authentication import TokenAuthentication

from drf_spectacular.openapi import OpenApiAuthenticationExtension

from knox.auth import TokenAuthentication as KnoxTokenAuthentication


class APIKeyAuthentication(TokenAuthentication):
    def authenticate(self, request):
        # Custom logic to check for a different header or token parameter
        token = request.META.get("HTTP_X_API_KEY")
        if not token:
            return None

        return self.authenticate_credentials(token)


class KnoxTokenAuthExtension(OpenApiAuthenticationExtension):
    target_class = KnoxTokenAuthentication
    name = "TokenAuthentication"  # Name to use in the generated schema

    def get_security_definition(self, auto_schema):
        return {"type": "apiKey", "in": "header", "name": "Authorization"}

    def get_security_requirements(self, auto_schema):
        return [{self.name: []}]


class APIKeyAuthExtension(OpenApiAuthenticationExtension):
    target_class = APIKeyAuthentication
    name = "APIKeyAuthentication"

    def get_security_definition(self, auto_schema):
        return {"type": "apiKey", "in": "header", "name": "Authorization"}

    def get_security_requirements(self, auto_schema):
        return [{self.name: []}]
