import os
from django import template

register = template.Library()

@register.filter
def basename(value):
    """
    Retorna apenas o nome do arquivo sem o caminho completo.
    """
    return os.path.basename(value)

@register.filter
def get_item(dictionary, key):
    """Retorna o valor de um dicionário para uma chave específica."""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def dict_get(d, key):
    return d.get(key)