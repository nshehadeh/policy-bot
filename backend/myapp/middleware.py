from django.utils.deprecation import MiddlewareMixin

class DisableGZipForEventStream(MiddlewareMixin):
    def process_response(self, request, response):
        # Disable GZip for Server-Sent Event (SSE) streams
        if response.get('Content-Type') == 'text/event-stream':
            response['Content-Encoding'] = ''
        return response