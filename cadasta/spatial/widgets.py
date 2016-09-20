from django.forms.widgets import Widget
from django.utils.translation import ugettext as _
from party.models import Party


class SelectPartyWidget(Widget):
    def __init__(self, project, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project

    def render(self, name, value, attrs={}):
        prj_parties = Party.objects.filter(project_id=self.project)
        parties = [
            '<option value="' + p.id + '" data-type="' +
            p.get_type_display() + '"' +
            (' selected="selected"' if p.id == value else '') + '>' +
            p.name + '</option>' for p in prj_parties
        ]

        return (
            '<select id="party-select" name="{name}" class="form-control" '
            '       data-parsley-required="true">'
            '<option value="" data-type="">' +
            _("Please select a party") + '</option>'
            '{parties}'
            '</select>'
        ).format(parties=''.join(parties), name=name)


class NewEntityWidget(Widget):
    class Media:
        js = ('/static/js/rel_new_item.js',)

    def render(self, name, value, attrs={}):
        html = (
            '<button class="btn btn-default" id="add-party" type="button">'
            '<span class="glyphicon glyphicon-plus" aria-hidden="true">'
            '</span> {button_text}</button>'
            '<input id="new_entity_field" type="hidden"'
            '       name="{name}" value="{value}">'
        )
        button_text = _("Add party")

        return html.format(name=name,
                           value=(value if value else ''),
                           button_text=button_text)
