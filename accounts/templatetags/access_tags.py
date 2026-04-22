from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Permite acessar dicionários por chave variável nos templates: dict|get_item:key"""
    return dictionary.get(key)
