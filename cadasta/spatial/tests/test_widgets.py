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
        assert '<input type="hidden" name="name" value="value">' in rendered
        assert ('<tr data-id="' + party_1.id + '"><td>' + party_1.name + ''
                '</td><td>' + party_1.get_type_display() + '</td><tr>'
                in rendered)
        assert ('<tr data-id="' + party_2.id + '"><td>' + party_2.name + ''
                '</td><td>' + party_2.get_type_display() + '</td><tr>'
                in rendered)


class NewEntityWidgetTest(TestCase):
    def test_render_value(self):
        widget = NewEntityWidget()
        expected = (
            '<button class="btn btn-block btn-primary"'
            '        id="add_btn" type="button">Add new party</button>'
            '<input id="new_enitity_field" type="hidden"'
            '       name="name" value="value">'
        )
        rendered = widget.render(name='name', value='value')
        assert rendered == expected

    def test_render_no_value(self):
        widget = NewEntityWidget()
        expected = (
            '<button class="btn btn-block btn-primary"'
            '        id="add_btn" type="button">Add new party</button>'
            '<input id="new_enitity_field" type="hidden"'
            '       name="name" value="">'
        )
        rendered = widget.render(name='name', value=None)
        assert rendered == expected
