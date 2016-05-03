import json
from django.test import TestCase
from pytest import raises

from .. import forms
from ..models import Organization, OrganizationRole, ProjectRole
from .factories import OrganizationFactory, ProjectFactory

from accounts.tests.factories import UserFactory


class OrganzationAddTest(TestCase):
    def _save(self, data, count=1):
        form = forms.OrganizationForm(data, user=UserFactory.create())
        form.save()
        assert form.is_valid() is True
        assert Organization.objects.count() == count

    def test_add_organization(self):
        data = {
            'name': 'Org',
            'description': 'Org description',
            'urls': '',
            'contacts': ''
        }
        self._save(data)
        org = Organization.objects.first()

        assert org.slug == 'org'
        assert OrganizationRole.objects.filter(organization=org).count() == 1

    def test_unique_slugs(self):
        data = {
            'name': 'Org',
            'description': 'Org description #1',
            'urls': '',
            'contacts': ''
        }
        self._save(data)
        org1 = Organization.objects.first()
        assert org1.slug == 'org'
        data['description'] = 'Org description #2'
        self._save(data, count=2)
        orgs = Organization.objects.all()
        assert len(orgs) == 2
        assert orgs[0].slug != orgs[1].slug

    def test_add_organization_with_url(self):
        data = {
            'name': 'Org',
            'description': 'Org description',
            'urls': 'http://example.com',
            'contacts': ''
        }
        self._save(data)
        org = Organization.objects.first()
        assert org.urls == ['http://example.com']

    def test_add_organization_with_contact(self):
        data = {
            'name': 'Org',
            'description': 'Org description',
            'urls': 'http://example.com',
            'contacts': json.dumps([{'name': 'Ringo Starr',
                                     'tel': '555-5555'}])
        }
        self._save(data)
        org = Organization.objects.first()
        assert org.contacts == [{'name': 'Ringo Starr', 'tel': '555-5555'}]

    def test_update_organization(self):
        org = OrganizationFactory.create(slug='some-org')

        data = {
            'name': 'Org',
            'description': 'Org description',
            'urls': '',
            'contacts': ''
        }
        form = forms.OrganizationForm(data, instance=org)
        form.save()

        org.refresh_from_db()

        assert form.is_valid() is True
        assert org.name == data['name']
        assert org.description == data['description']
        assert org.slug == 'some-org'


class AddOrganizationMemberFormTest(TestCase):
    def _save(self, identifier=None, identifier_field=None, ok=True):
        org = OrganizationFactory.create()
        user = UserFactory.create()
        if identifier_field is not None:
            identifier = getattr(user, identifier_field)
        data = {'identifier': identifier}
        form = forms.AddOrganizationMemberForm(data, organization=org)
        if ok:
            form.save()
            assert form.is_valid() is True
            assert OrganizationRole.objects.filter(
                organization=org, user=user).count() == 1
        else:
            with raises(ValueError):
                form.save()
            assert form.is_valid() is False
            assert OrganizationRole.objects.count() == 0

    def test_add_with_username(self):
        self._save(identifier_field='username')

    def test_add_with_email(self):
        self._save(identifier_field='email')

    def test_add_non_existing_user(self):
        self._save(identifier='some-user', ok=False)


class EditOrganizationMemberFormTest(TestCase):
    def test_edit_org_role(self):
        org = OrganizationFactory.create()
        user = UserFactory.create()

        data = {'org_role': 'A'}

        org_role = OrganizationRole.objects.create(organization=org, user=user)
        form = forms.EditOrganizationMemberForm(data, org, user)

        form.save()
        org_role.refresh_from_db()

        assert form.is_valid() is True
        assert org_role.admin is True

    def test_edit_project_roles(self):
        user = UserFactory.create()
        org = OrganizationFactory.create()
        prj_1 = ProjectFactory.create(organization=org)
        prj_2 = ProjectFactory.create(organization=org)
        prj_3 = ProjectFactory.create(organization=org)
        prj_4 = ProjectFactory.create(organization=org)

        org_role = OrganizationRole.objects.create(organization=org, user=user)
        ProjectRole.objects.create(project=prj_4, user=user, role='PM')

        data = {
            'org_role': 'M',
            prj_1.id: 'DC',
            prj_2.id: 'PU',
            prj_3.id: 'Pb',
            prj_4.id: 'Pb'
        }

        form = forms.EditOrganizationMemberForm(data, org, user)

        form.save()
        org_role.refresh_from_db()

        assert form.is_valid() is True
        assert org_role.admin is False
        assert ProjectRole.objects.get(user=user, project=prj_1).role == 'DC'
        assert ProjectRole.objects.get(user=user, project=prj_2).role == 'PU'
        assert (ProjectRole.objects.filter(user=user, project=prj_3).exists()
                is False)
        assert (ProjectRole.objects.filter(user=user, project=prj_4).exists()
                is False)
