from django import template
from knowledge.models import Section

register = template.Library()

@register.inclusion_tag('knowledge/tree_navigation.html')
def section_tree():
    """Отображает древовидную навигацию разделов"""
    sections = Section.objects.filter(is_active=True).order_by('parent__title', 'title')
    tree = {}
    
    for section in sections:
        if section.parent is None:
            if section.id not in tree:
                tree[section.id] = {
                    'section': section,
                    'children': []
                }
        else:
            if section.parent.id not in tree:
                tree[section.parent.id] = {
                    'section': section.parent,
                    'children': []
                }
            tree[section.parent.id]['children'].append(section)
    
    return {'sections_tree': tree.values()}