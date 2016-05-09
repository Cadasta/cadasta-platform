from django.forms import Select, Widget
from django.utils.translation import ugettext as _


class ProjectRoleWidget(Select):
    html = (
        '<tr>'
        '  <td>'
        '    <p>{full_name}</p>'
        '    <p>{username}</p>'
        '  </td>'
        '  <td>{email}</td>'
        '  <td>'
        '    {select}'
        '  </td>'
        '</tr>'
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def render(self, name, value, attrs=None, choices=()):
        if value == 'A':
            select = _("Administrator")
        else:
            select = super().render(name, value, attrs=attrs, choices=choices)

        return self.html.format(
            full_name=self.user.full_name,
            username=self.user.username,
            email=self.user.email,
            select=select
        )


class PublicPrivateToggle(Widget):
    html = (
        '<div class="public-private-widget">'
        '  <label for"{name}">{label}</label>'
        '  <div>'
        '    {public}<br>'
        '    <span class="glyphicon glyphicon-eye-open"></span>'
        '  </div>'
        '  <div>'
        '    <input name="{name}" {checked} type="checkbox"'
        '           data-toggle="toggle" data-onstyle="danger"'
        '           data-offstyle="success" data-on=" " data-off=" ">'
        '  </div>'
        '  <div>'
        '    {private}<br>'
        '    <span class="glyphicon glyphicon-eye-close"></span>'
        '  </div>'
        '</div>'
    )

    class Media:
        js = (
            'https://gitcdn.github.io/bootstrap-toggle/2.2.2/js/'
            'bootstrap-toggle.min.js',
        )
        css = {
            'all': (
                'https://gitcdn.github.io/bootstrap-toggle/2.2.2/css/'
                'bootstrap-toggle.min.css',
            )
        }

    def render(self, name, value, attrs=None):
        return self.html.format(
            label=_("Project visibility"),
            name=name,
            public=_("Public"),
            private=_("Private"),
            checked=('checked' if value != 'public' else '')
        )
