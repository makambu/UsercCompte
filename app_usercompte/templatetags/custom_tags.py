from django import template
from django.forms.boundfield import BoundField

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


def add_class(field, css_class):
    if isinstance(field, BoundField):
        return field.as_widget(attrs={"class": css_class})
    return field  # retourne tel quel si ce n’est pas un champ
