from django.forms.widgets import HiddenInput
from party.models import Party


class SelectPartyWidget(HiddenInput):
    def __init__(self, project, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project

    def render(self, name, value, attrs={}):
        prj_parties = Party.objects.filter(project_id=self.project)
        parties = ['<tr data-id="' + p.id + '"><td>' + p.name + '</td>'
                   '<td>' + p.get_type_display() + '</td><tr>'
                   for p in prj_parties]

        return (
            '<table class="table" id="select-list">'
            '  <thead>'
            '    <tr>'
            '      <th>Party</th>'
            '      <th>Type</th>'
            '    </tr>'
            '  </thead>'
            '  <tbody>'
            '    {parties}'
            '  </tbody>'
            '</table>'
            '<input type="hidden" name="{name}" value="{value}">'
        ).format(parties=''.join(parties),
                 name=name,
                 value=value or '')


class NewEntityWidget(HiddenInput):
    class Media:
        js = ('/static/js/rel_new_item.js',)

    def render(self, name, value, attrs={}):
        html = (
            '<button class="btn btn-link"'
            '        id="add-party" type="button">Add party</button>'
            '<input id="new_entity_field" type="hidden"'
            '       name="{name}" value="{value}">'
        )

        return html.format(name=name, value=(value if value else ''))
