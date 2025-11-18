from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css):
    """
    Adds a CSS class to a Django form field widget
    Usage: {{ form.field|add_class:"your-css-classes" }}
    """
    existing_classes = field.field.widget.attrs.get('class', '')
    new_classes = f"{existing_classes} {css}".strip()
    return field.as_widget(attrs={'class': new_classes})


@register.filter(name='attr')
def attr(field, attribute):
    """
    Add HTML attribute to form field
    Usage: {{ form.field|attr:"maxlength:100" }}
    Multiple attributes: {{ form.field|attr:"maxlength:100"|attr:"pattern:[0-9]*" }}
    """
    if ':' not in str(attribute):
        return field
    
    attr_name, attr_value = str(attribute).split(':', 1)
    
    # Get existing attributes from the widget
    existing_attrs = field.field.widget.attrs.copy()
    
    # Add the new attribute
    existing_attrs[attr_name] = attr_value
    
    # Return the field with updated attributes
    return field.as_widget(attrs=existing_attrs)


@register.filter(name='add_error_class')
def add_error_class(field, css_class='border-red-500'):
    """
    Add error class to field if it has errors
    Usage: {{ form.field|add_error_class }}
    Custom class: {{ form.field|add_error_class:"border-red-600" }}
    """
    if field.errors:
        existing_class = field.field.widget.attrs.get('class', '')
        new_class = f"{existing_class} {css_class}".strip()
        return field.as_widget(attrs={'class': new_class})
    return field


@register.filter(name='placeholder')
def placeholder(field, text):
    """
    Add placeholder text to form field
    Usage: {{ form.field|placeholder:"Enter your name" }}
    """
    return field.as_widget(attrs={'placeholder': text})


@register.filter(name='add_attrs')
def add_attrs(field, attrs_string):
    """
    Add multiple attributes at once
    Usage: {{ form.field|add_attrs:"maxlength:100,pattern:[A-Za-z]*,title:Only letters" }}
    """
    if not attrs_string:
        return field
    
    existing_attrs = field.field.widget.attrs.copy()
    
    # Parse the attributes string
    attrs_list = attrs_string.split(',')
    for attr_pair in attrs_list:
        if ':' in attr_pair:
            attr_name, attr_value = attr_pair.split(':', 1)
            existing_attrs[attr_name.strip()] = attr_value.strip()
    
    return field.as_widget(attrs=existing_attrs)