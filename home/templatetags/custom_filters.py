import os
from django import template

register = template.Library()

@register.filter
def basename(value):
    """
    Retorna apenas o nome do arquivo sem o caminho completo.
    """
    return os.path.basename(value)
