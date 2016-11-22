from pytest import raises
from django.test import TestCase
from django.forms import formset_factory, ValidationError

from accounts.tests.factories import UserFactory

from organization import fields as org_fields
from ..forms import ContactsForm


class ProjectRoleFieldTest(TestCase):
    def test_init(self):
        user = UserFactory.build()
        choices = (('Ab', 'Ahh Bee',),)
        field = org_fields.ProjectRoleField(user, choices=choices)
        assert field.widget.user == user
        assert field.widget.choices == [choices[0]]


class ProjectRoleEditFieldTest(TestCase):
    def test_init(self):
        choices = (('Ab', 'Ahh Bee',),)
        admin = True
        field = org_fields.ProjectRoleEditField(admin, choices=choices)
        assert field.widget.admin == admin
        assert field.widget.choices == [choices[0]]


class PublicPrivateFieldTest(TestCase):
    def test_clean(self):
        field = org_fields.PublicPrivateField()
        assert field.clean(None) == 'public'
        assert field.clean('on') == 'private'


class ContactsFieldTest(TestCase):
    def test_init(self):
        field = org_fields.ContactsField(form=ContactsForm)
        assert isinstance(field.formset, type(formset_factory(ContactsForm)))

    def test_clean(self):
        ContactFormset = formset_factory(form=ContactsForm)
        value = ContactFormset({
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '1',
            'form-MAX_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-name': 'Ringo',
            'form-0-email': 'ringo@beatles.uk',
            'form-0-tel': '555-555',
            'form-1-name': 'john',
            'form-1-email': 'john@beatles.uk',
            'form-1-tel': '555-555',
            'form-1-remove': True,
            'form-2-name': '',
            'form-2-email': '',
            'form-2-tel': '',
        })
        field = org_fields.ContactsField(form=ContactsForm)
        expected = [{
            'name': 'Ringo',
            'email': 'ringo@beatles.uk',
            'tel': '555-555'
        }]
        assert field.clean(value) == expected

    def test_invalid_clean(self):
        ContactFormset = formset_factory(form=ContactsForm)
        value = ContactFormset({
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '1',
            'form-MAX_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-name': 'Ringo',
            'form-0-email': 'ringo@beatles',
            'form-0-tel': '',
            'form-1-name': '',
            'form-1-email': '',
            'form-1-tel': ''
        })
        field = org_fields.ContactsField(form=ContactsForm)
        with raises(ValidationError):
            field.clean(value)

    def test_widget_attr(self):
        field = org_fields.ContactsField(form=ContactsForm)
        widget_attrs = field.widget_attrs('widget')
        assert widget_attrs == {'formset': field.formset}
