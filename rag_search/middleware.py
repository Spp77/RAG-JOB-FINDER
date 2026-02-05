import jwt
import requests
import json
from django.conf import settings
from django.http import JsonResponse
from cryptography.hazmat.primitives import serialization
from jwt.algorithms import RSAAlgorithm

import logging

logger = logging.getLogger(__name__)

class ClerkMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwks_client = None

    def __call__(self, request):
        # Only protect specific paths, e.g., /api/mcp/ or /api/v1/protected/
        if request.path.startswith('/api/mcp/') or request.path.startswith('/api/tools/'):
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return JsonResponse({"error": "Missing Authorization Header"}, status=401)
            
            token = auth_header.split(' ')[1]
            try:
                decoded = self.verify_clerk_token(token)
                request.clerk_user = decoded
            except Exception as e:
                logger.error(f"Clerk Auth Failed: {e}")
                return JsonResponse({"error": "Invalid Token", "details": str(e)}, status=403)

        return self.get_response(request)

    def verify_clerk_token(self, token):
        # Minimal JWKS verification logic
        # In prod, cache the JWKS keys
        jwks_url = settings.CLERK_JWKS_URL # e.g., https://api.clerk.dev/v1/jwks or from dashboard
        if not jwks_url:
             # If no URL configured (dev mode without keys), optionally skip or fail
             # For this demo, we'll fail if not set, prompting user to config.
             raise Exception("CLERK_JWKS_URL not configured in settings")

        jwks = requests.get(jwks_url).json()
        public_keys = {}
        for jwk in jwks['keys']:
            kid = jwk['kid']
            public_keys[kid] = RSAAlgorithm.from_jwk(json.dumps(jwk))
        
        kid = jwt.get_unverified_header(token)['kid']
        key = public_keys.get(kid)
        
        return jwt.decode(token, key=key, algorithms=['RS256'])
