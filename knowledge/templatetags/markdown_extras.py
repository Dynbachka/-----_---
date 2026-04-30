from django import template
from django.template.defaultfilters import stringfilter
import markdown as md

register = template.Library()

@register.filter()
@stringfilter
def markdown(value):
    # Расширения: 'extra' для таблиц/списков, 'codehilite' для подсветки кода
    return md.markdown(value, extensions=['extra', 'codehilite', 'toc'])