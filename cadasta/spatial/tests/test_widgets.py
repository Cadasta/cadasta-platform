from django.test import TestCase
from organization.tests.factories import ProjectFactory
from party.tests.factories import PartyFactory
from ..widgets import NewEntityWidget, SelectPartyWidget


class SelectPartyWidgetTest(TestCase):
    def test_render(self):
        project = ProjectFactory.create()
        party_1 = PartyFactory.create(project=project)
        party_2 = PartyFactory.create(project=project)

        widget = SelectPartyWidget(project=project)
        rendered = widget.render(name='name', value='value')
        assert ('<select id="party-select" name="name" class="form-control" '
                '       data-parsley-required="true">' in rendered)
        assert ('<option value="' + party_1.id + '" data-type="'
                '' + party_1.get_type_display() + '">' + party_1.name + ''
                '</option>' in rendered)
        assert ('<option value="' + party_2.id + '" data-type="'
                '' + party_2.get_type_display() + '">' + party_2.name + ''
                '</option>' in rendered)


class NewEntityWidgetTest(TestCase):
    def test_render_value(self):
        widget = NewEntityWidget()
        expected = (
            '<button class="btn btn-default" id="add-party" type="button">'
            '<span class="glyphicon glyphicon-plus" aria-hidden="true">'
            '</span> Add party</button>'
            '<input id="new_entity_field" type="hidden"'
            '       name="name" value="value">'
        )
        rendered = widget.render(name='name', value='value')
        assert rendered == expected

    def test_render_no_value(self):
        widget = NewEntityWidget()
        expected = (
            '<button class="btn btn-default" id="add-party" type="button">'
            '<span class="glyphicon glyphicon-plus" aria-hidden="true">'
            '</span> Add party</button>'
            '<input id="new_entity_field" type="hidden"'
            '       name="name" value="">'
        )
        rendered = widget.render(name='name', value=None)
        assert rendered == expected
