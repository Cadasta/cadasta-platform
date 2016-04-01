import json
from django.test import TestCase
from pytest import raises

from .. import forms
from ..models import Organization, OrganizationRole, ProjectRole
from .factories import OrganizationFactory, ProjectFactory

from accounts.tests.factories import UserFactory


class OrganzationAddTest(TestCase):
    def test_add_organization(self):
        data = {
            'name': 'Org',
            'description': 'Org description',
            'urls': '',
            'contacts': ''
        }
        form = forms.OrganizationForm(data, user=UserFactory.create())
        form.save()

        assert form.is_valid() is True
        assert Organization.objects.count() == 1

        org = Organization.objects.first()
        assert org.slug == 'org'
        assert OrganizationRole.objects.filter(organization=org).count() == 1

    def test_add_organization_with_url(self):
        data = {
            'name': 'Org',
            'description': 'Org description',
            'urls': 'http://example.com',
            'contacts': ''
        }
        form = forms.OrganizationForm(data, user=UserFactory.create())
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
        form = forms.OrganizationForm(data, user=UserFactory.create())
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
        form = forms.OrganizationForm(data, instance=org)
        form.save()

        org.refresh_from_db()

        assert form.is_valid() is True
        assert org.name == data['name']
        assert org.description == data['description']
        assert org.slug == 'some-org'


class AddOrganizationMemberFormTest(TestCase):
    def test_add_with_username(self):
        org = OrganizationFactory.create()
        user = UserFactory.create()

        data = {'identifier': user.username}
        form = forms.AddOrganizationMemberForm(data, organization=org)

        form.save()

        assert form.is_valid() is True
        assert OrganizationRole.objects.filter(
            organization=org, user=user).count() == 1

    def test_add_with_email(self):
        org = OrganizationFactory.create()
        user = UserFactory.create()

        data = {'identifier': user.email}
        form = forms.AddOrganizationMemberForm(data, organization=org)

        form.save()

        assert form.is_valid() is True
        assert OrganizationRole.objects.filter(
            organization=org, user=user).count() == 1

    def test_add_non_existing_user(self):
        org = OrganizationFactory.create()

        data = {'identifier': 'some-user'}
        form = forms.AddOrganizationMemberForm(data, organization=org)

        with raises(ValueError):
            form.save()

        assert form.is_valid() is False
        assert OrganizationRole.objects.count() == 0


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
