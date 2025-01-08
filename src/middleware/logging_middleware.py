from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from src.services.request_logger import RequestLogger
import time
import json

class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.logger = RequestLogger()

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Capture request data
        request_data = {
            'endpoint': str(request.url),
            'method': request.method,
            'query_params': dict(request.query_params),
            'path_params': request.path_params,
        }

        # Try to get request body if present
        try:
            body = await request.body()
            if body:
                request_data['body'] = json.loads(body)
        except:
            pass

        # Process request and capture response
        response = await call_next(request)
        duration = round((time.time() - start_time) * 1000, 2)

        # Log the interaction
        await self.logger.log_interaction({
            'endpoint': str(request.url),
            'method': request.method,
            'request_data': request_data,
            'response': {
                'status_code': response.status_code,
                'headers': dict(response.headers)
            },
            'duration': duration,
            'status': 'success' if response.status_code < 400 else 'error'
        })

        return response
