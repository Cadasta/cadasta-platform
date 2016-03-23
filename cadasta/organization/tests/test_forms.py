import json
from django.test import TestCase

from ..forms import OrganizationForm
from ..models import Organization
from .factories import OrganizationFactory


class OrganzationAddTest(TestCase):
    def test_add_organization(self):
        data = {
            'name': 'Org',
            'description': 'Org description',
            'urls': '',
            'contacts': ''
        }
        form = OrganizationForm(data)
        form.save()

        assert form.is_valid() is True
        assert Organization.objects.count() == 1

        org = Organization.objects.first()
        assert org.slug

    def test_add_organization_with_url(self):
        data = {
            'name': 'Org',
            'description': 'Org description',
            'urls': 'http://example.com',
            'contacts': ''
        }
        form = OrganizationForm(data)
        form.save()

        assert form.is_valid() is True
        assert Organization.objects.count() == 1

        org = Organization.objects.first()
        assert org.urls == ['http://example.com']

    def test_add_organization_with_contact(self):
        data = {
            'name': 'Org',
            'description': 'Org description',
            'urls': 'http://example.com',
            'contacts': json.dumps([{
                'name': 'Ringo Starr',
                'tel': '555-5555'
            }])
        }
        form = OrganizationForm(data)
        form.save()

        assert form.is_valid() is True
        assert Organization.objects.count() == 1

        org = Organization.objects.first()
        assert org.contacts == [{
            'name': 'Ringo Starr',
            'tel': '555-5555'
        }]

    def test_update_organization(self):
        org = OrganizationFactory.create(**{'slug': 'some-org'})

        data = {
            'name': 'Org',
            'description': 'Org description',
            'urls': '',
            'contacts': ''
        }
        form = OrganizationForm(data, instance=org)
        form.save()

        org.refresh_from_db()

        assert form.is_valid() is True
        assert org.name == data['name']
        assert org.description == data['description']
        assert org.slug == 'some-org'
