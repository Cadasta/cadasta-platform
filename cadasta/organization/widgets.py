from django.forms import Select, Widget
from django.utils.translation import ugettext as _


class ProjectRoleWidget(Select):
    html = (
        '<tr>'
        '  <td>'
        '    <p>{full_name}</p>'
        '    <p>{username}</p>'
        '  </td>'
        '  <td class="hidden-xs hidden-sm">{email}</td>'
        '  <td>'
        '    {select}'
        '  </td>'
        '</tr>'
    )

    def __init__(self, user, role, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.role = role

    def render(self, name, value, attrs=None, choices=()):
        if value == 'A' or self.role == 'A':
            select = _("Administrator")
        else:
            select = super().render(name, value, attrs=attrs, choices=choices)

        return self.html.format(
            full_name=self.user.full_name,
            username=self.user.username,
            email=self.user.email,
            select=select
        )


class OrganizationRoleWidget(Select):
    html = (
        '<tr>'
        '  <td>'
        '    <p>{project}</p>'
        '  </td>'
        '  <td>'
        '    {select}'
        '  </td>'
        '</tr>'
    )

    def __init__(self, project, role, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        self.role = role

    def render(self, project, value, attrs=None, choices=()):
        if value == 'A' or self.role == 'A':
            select = _("Administrator")
        else:
            select = super().render(project, value,
                                    attrs=attrs,
                                    choices=choices)

        return self.html.format(
            project=self.project,
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
            checked=('checked' if value in ['private', 'on'] else '')
        )


class ContactsWidget(Widget):
    html = (
        '<table class="table contacts-form">'
        '  <thead>'
        '    <tr>'
        '      <th>{name}</th>'
        '      <th>{email}</th>'
        '      <th>{phone}</th>'
        '      <th></th>'
        '    </tr>'
        '  </thead>'
        '  <tbody>'
        '    {table}'
        '  </tbody>'
        '  <tfoot>'
        '    <tr>'
        '      <td colspan="4">'
        '        <button data-prefix="{prefix}" type="button" '
        '                class="btn btn-default btn-sm" '
        '                id="add-contact"><span class="glyphicon '
        '                glyphicon-plus" aria-hidden="true"></span> '
        '                {add_contact}</button>'
        '      </td>'
        '    </tr>'
        '  </tfoot>'
        '</table>'
    )

    class Media:
        js = (
            '/static/js/contacts.js',
        )

    def value_from_datadict(self, data, files, name):
        return self.attrs['formset'](data, files, prefix=name)

    def render(self, name, value, attrs=None):
        if not isinstance(value, self.attrs['formset']):
            value = self.attrs['formset'](prefix=name, initial=value)

        # This is a bit naughty: Here we're passing on the widget's HTML class
        # attributes to each field in each form of the formset. This is
        # necessary to render the fields using bootstrap styles.
        if attrs and 'class' in attrs:
            for form in value.forms:
                for field in form:
                    widget_attrs = {}
                    if field.field.widget.attrs:
                        widget_attrs = field.field.widget.attrs.copy()
                    widget_attrs['class'] = attrs['class']
                    field.field.widget.attrs = widget_attrs

        return self.html.format(
            name=_("Name"),
            phone=_("Phone"),
            email=_("Email"),
            add_contact=_("Add contact"),
            table=value,
            prefix=name
        )
