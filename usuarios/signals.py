"""
    Señales para el logging
"""

import logging
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver

logger = logging.getLogger('access_logger')

def get_ip(request):
    """
    Obtenemos la dirección IP del request
    """
    return request.META.get('REMOTE_ADDR', '')

@receiver(user_logged_in)
def log_login_success(sender, request, user, **kwargs):
    # Las funciones f-string no es la forma de trabajar mas eficiente
    # con funciones de registro
    # logger.info(f"LOGIN SUCCESS - {user.username} - IP: {get_ip(request)}")
    logger.info("LOGIN SUCCESS - %s - IP: %s", user.username, get_ip(request))

@receiver(user_login_failed)
def log_login_failure(sender, credentials, request, **kwargs):
    username = credentials.get('username', 'UNKNOWN')
    logger.warning(f"LOGIN FAILED - {username} - IP: {get_ip(request)}")

