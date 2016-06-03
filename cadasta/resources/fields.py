from django.forms import BooleanField
from .widgets import ResourceWidget


class ResourceField(BooleanField):
    def __init__(self, resource, widget=None, *args, **kwargs):
        widget = widget or ResourceWidget(resource=resource)
        super().__init__(widget=widget, required=False, *args, **kwargs)
        self.resource = resource
