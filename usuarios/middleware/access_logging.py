"""
Middleware para el registro de logs
"""
import logging
from datetime import datetime

logger = logging.getLogger('access_logger')


class AccessLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = self.get_client_ip(request)
        user = request.user if request.user.is_authenticated else 'Anonymous'
        path = request.path
        method = request.method
        logger.info(f'{datetime.now()} - {ip} - {user} - {method} {path}')
        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
