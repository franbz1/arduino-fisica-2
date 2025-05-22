from django import template

register = template.Library()

@register.filter
def index(list_obj, i):
    """
    Filtro para acceder a elementos por índice en listas
    
    Ejemplo:
        {{ my_list|index:0 }}
    """
    try:
        return list_obj[i]
    except (IndexError, TypeError):
        return "" 