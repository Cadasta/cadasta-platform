import datetime
from django import forms
from django.test import TestCase
from core.templatetags import filters
from django.core.files.uploadedfile import SimpleUploadedFile


class MockForm(forms.Form):

    TYPE_CHOICES = (('IN', 'Individual'),
                    ('CO', 'Corporation'),
                    ('GR', 'Group'))

    name = forms.CharField()
    type = forms.ChoiceField(choices=TYPE_CHOICES, initial='IN')
    is_true = forms.BooleanField(
        required=True, widget=forms.widgets.CheckboxInput
    )
    file = forms.FileField()
    date = forms.DateField(initial=datetime.datetime.now)


class FilterTest(TestCase):

    def setUp(self):
        super().setUp()
        self.data = {
            'name': 'Cadasta',
            'type': 'GR',
            'is_true': False
        }

    def test_display_choice_verbose(self):
        form = MockForm(data=self.data)
        field = form.fields.get('type')
        bf = forms.BoundField(form, field, 'type')
        value = filters.display_choice_verbose(bf)
        assert value == 'Group'

    def test_field_value(self):
        form = MockForm(data=self.data)
        field = form.fields.get('type')
        bf = forms.BoundField(form, field, 'type')
        value = filters.field_value(bf)
        assert value == 'GR'

    def test_field_value_file_field(self):
        form = MockForm(
            data=self.data,
            files={'file': SimpleUploadedFile('test.txt', b'some content')}
        )
        field = form.fields.get('file')
        bf = forms.BoundField(form, field, 'file')
        value = filters.field_value(bf)
        assert value.name == 'test.txt'

    def test_blank_file_field(self):
        form = MockForm(data=self.data)
        field = form.fields.get('file')
        bf = forms.BoundField(form, field, 'file')
        value = filters.field_value(bf)
        assert value == ''

    def test_field_value_as_callable(self):
        form = MockForm()
        field = form.fields.get('date')
        bf = forms.BoundField(form, field, 'date')
        value = filters.field_value(bf)
        assert isinstance(value, datetime.datetime)

    def test_set_parsley_required(self):
        form = MockForm(data={'name', 'Test'})
        field = form.fields.get('type')
        bf = forms.BoundField(form, field, 'type')
        filters.set_parsley_required(bf)
        assert bf.field.widget.attrs == {'data-parsley-required': 'true'}

    def test_set_parsley_sanitize(self):
        form = MockForm(data={'name', 'Test'})
        field = form.fields.get('name')
        bf = forms.BoundField(form, field, 'name')
        filters.set_parsley_sanitize(bf)
        assert bf.field.widget.attrs == {'data-parsley-sanitize': '1'}
