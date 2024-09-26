from django.utils.deprecation import MiddlewareMixin

class DisableGZipForEventStream(MiddlewareMixin):
    def process_response(self, request, response):
        # Disable GZip for Server-Sent Event (SSE) streams
        if response.get('Content-Type') == 'text/event-stream':
            if 'Content-Encoding' in response:
                del response['Content-Encoding']  # Remove the Content-Encoding header
        return response