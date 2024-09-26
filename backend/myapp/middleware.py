from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token
from urllib.parse import parse_qs
from channels.db import database_sync_to_async


class DisableGZipForEventStream(MiddlewareMixin):
    def process_response(self, request, response):
        # Disable GZip for Server-Sent Event (SSE) streams
        if response.get('Content-Type') == 'text/event-stream':
            if 'Content-Encoding' in response:
                del response['Content-Encoding']  # Remove the Content-Encoding header
        return response
    
@database_sync_to_async
def get_user(token_key):
    try:
        token = Token.objects.get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return AnonymousUser()

class TokenAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = scope['query_string'].decode('utf-8')
        query_params = parse_qs(query_string)
        token_key = query_params.get('token', [None])[0]

        scope['user'] = await get_user(token_key)

        return await self.inner(scope, receive, send)