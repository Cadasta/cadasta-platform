from django.forms import ChoiceField, CharField
from .widgets import ProjectRoleWidget, PublicPrivateToggle


class ProjectRoleField(ChoiceField):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        choices = kwargs.get('choices', ())
        self.widget = ProjectRoleWidget(user=user, choices=choices)


class PublicPrivateField(CharField):
    def __init__(self, *args, **kwargs):
        super().__init__(widget=PublicPrivateToggle, *args, **kwargs)

    def clean(self, value):
        if value:
            value = 'private'
        else:
            value = 'public'
        return value
