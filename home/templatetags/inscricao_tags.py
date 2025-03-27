from django import template
register = template.Library()

@register.filter
def has_selecao(inscricoes, selecao):
    return any(inscricao.selecao == selecao for inscricao in inscricoes)