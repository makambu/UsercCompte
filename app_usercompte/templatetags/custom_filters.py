from django import template
import os

register = template.Library()

@register.filter
def endswith(value, suffix):
    return str(value).endswith(suffix)

@register.filter
def basename(value):
    return os.path.basename(str(value))


@register.filter
def get(dictionary, key):
    return dictionary.get(key)

@register.filter
def dict_get(dict_obj, key):
    return dict_obj.get(key)

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)