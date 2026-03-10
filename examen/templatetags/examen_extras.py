"""Filtros de template personalizados para la app examen."""
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Permite acceder a un diccionario por clave en los templates.
    Uso: {{ mi_dict|get_item:clave }}
    """
    if not isinstance(dictionary, dict):
        return None
    return dictionary.get(key)
