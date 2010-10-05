from django import template
from datetime import timedelta

register = template.Library()

def timezone(value, offset):
  return value + timedelta(hours=offset)
register.filter(timezone)