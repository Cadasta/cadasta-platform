import os
import random
import pytest
from pytest import raises
from zipfile import ZipFile

from django.conf import settings
from django.forms.utils import ErrorDict
from django.test import TestCase

from buckets.test.storage import FakeS3Storage
from tutelary.models import Role

from .. import forms
from ..models import Organization, OrganizationRole, ProjectRole
from .factories import OrganizationFactory, ProjectFactory

from core.tests.utils.cases import UserTestCase
from core.tests.utils.files import make_dirs  # noqa
from questionnaires.tests.factories import QuestionnaireFactory
from questionnaires.exceptions import InvalidXLSForm
from accounts.tests.factories import UserFactory
from resources.tests.factories import ResourceFactory
from resources.tests.utils import clear_temp  # noqa
from resources.utils.io import ensure_dirs


class OrganizationTest(UserTestCase, TestCase):
    def setUp(self):
        super().setUp()
        self.data = {
            'name': 'Org',
            'description': 'Org description',
            'urls': '',
            'contacts-TOTAL_FORMS': 1,
            'contacts-INITIAL_FORMS': 0,
            'contacts-MIN_NUM_FORMS': 0,
            'contacts-MAX_NUM_FORMS': 1000,
            'contacts-0-name': '',
            'contacts-0-email': '',
            'contacts-0-tel': ''
        }

    def _save(self, data, count=1):
        form = forms.OrganizationForm(data, user=UserFactory.create())
        form.save()
        assert form.is_valid() is True
        assert Organization.objects.count() == count

    def test_add_organization(self):
        self._save(self.data)
        org = Organization.objects.first()
        assert org.slug == 'org'
        assert OrganizationRole.objects.filter(organization=org).count() == 1

    def test_duplicate_name_error(self):
        self.data['description'] = 'Org description #1'
        self._save(self.data)
        org1 = Organization.objects.first()
        assert org1.slug == 'org'

        self.data['description'] = 'Org description #2'
        form = forms.OrganizationForm(self.data, user=UserFactory.create())
        assert form.is_valid() is False
        assert form.errors == {
            'name': ["Organization with this Name already exists."]
        }
        assert Organization.objects.count() == 1

    # NOTE: This test is no longer possible because unique org names masks
    # the testing of unique org slugs via OrganizationForm. Unique org slugs
    # can only be tested via model unit tests.
    # def test_unique_slugs(self):
    #     self.data['description'] = 'Org description #1'
    #     self._save(self.data)
    #     org1 = Organization.objects.first()
    #     assert org1.slug == 'org'
    #
    #     self.data['description'] = 'Org description #2'
    #     self._save(self.data, count=2)
    #     orgs = Organization.objects.all()
    #     assert len(orgs) == 2
    #     assert orgs[0].slug != orgs[1].slug

    def test_add_organization_with_url(self):
        self.data['urls'] = 'http://example.com'
        self._save(self.data)
        org = Organization.objects.first()
        assert org.urls == ['http://example.com']

    def test_add_organization_with_semivalid_url(self):
        self.data['urls'] = 'example.com'
        self._save(self.data)
        org = Organization.objects.first()
        assert org.urls == ['http://example.com']

    def test_add_organization_with_invalid_url(self):
        self.data['urls'] = 'invalid url'
        form = forms.OrganizationForm(self.data, user=UserFactory.create())
        assert not form.is_valid()
        assert form.errors == {
            'urls': ["Enter a valid URL."]
        }

    def test_add_organization_with_contact(self):
        self.data['contacts-0-name'] = "Ringo Starr"
        self.data['contacts-0-email'] = 'ringo@beatles.uk'
        self.data['contacts-0-tel'] = '555-5555'
        self._save(self.data)
        org = Organization.objects.first()
        assert org.contacts == [{
            'name': "Ringo Starr",
            'tel': '555-5555',
            'email': 'ringo@beatles.uk'
        }]

    def test_add_organization_with_unicode_slug(self):
        self.data['name'] = "東京プロジェクト 2016"
        self._save(self.data)
        org = Organization.objects.first()
        assert org.slug == '東京プロジェクト-2016'

    def test_add_organization_with_restricted_name(self):
        invalid_names = ('add', 'ADD', 'Add', 'new', 'NEW', 'New')
        data = {
            'name': random.choice(invalid_names),
            'contacts-TOTAL_FORMS': 1,
            'contacts-INITIAL_FORMS': 0,
            'contacts-0-name': '',
            'contacts-0-email': '',
            'contacts-0-tel': ''
        }
        form = forms.OrganizationForm(data, user=UserFactory.create())
        assert not form.is_valid()
        assert form.errors == {
            'name': ["Organization name cannot be “Add” or “New”."]
        }
        assert not Organization.objects.exists()

    def test_update_organization(self):
        org = OrganizationFactory.create(slug='some-org')
        self.data['description'] = 'Org description'
        form = forms.OrganizationForm(self.data, instance=org)
        form.save()

        org.refresh_from_db()

        assert form.is_valid() is True
        assert org.name == self.data['name']
        assert org.description == self.data['description']
        assert org.slug == 'some-org'

    def test_update_organization_with_restricted_name(self):
        org = OrganizationFactory.create(slug='some-org')
        invalid_names = ('add', 'ADD', 'Add', 'new', 'NEW', 'New')
        self.data['name'] = random.choice(invalid_names)
        form = forms.OrganizationForm(self.data, instance=org)
        assert not form.is_valid()
        assert form.errors == {
            'name': ["Organization name cannot be “Add” or “New”."]
        }

    def test_remove_all_contacts(self):
        org = OrganizationFactory.create(
            slug='some-org',
            contacts=[{
                'name': 'User A',
                'email': 'a@example.com',
                'tel': ''
            }, {
                'name': 'User B',
                'email': '',
                'tel': '555-5555'
            }]
        )
        data = {
            'name': 'New Name',
            'contacts-TOTAL_FORMS': 3,
            'contacts-INITIAL_FORMS': 0,
            'contacts-MIN_NUM_FORMS': 0,
            'contacts-MAX_NUM_FORMS': 1000,
            'contacts-0-name': 'User A',
            'contacts-0-email': 'a@example.com',
            'contacts-0-tel': '',
            'contacts-0-remove': 'on',
            'contacts-1-name': 'User B',
            'contacts-1-email': '',
            'contacts-1-tel': '555-5555',
            'contacts-1-remove': 'on',
            'contacts-2-name': '',
            'contacts-2-email': '',
            'contacts-3-tel': ''
        }
        form = forms.OrganizationForm(data, instance=org)
        form.is_valid()
        form.save()
        org.refresh_from_db()
        assert org.contacts == []


class AddOrganizationMemberFormTest(UserTestCase, TestCase):
    def setUp(self):
        super().setUp()
        self.org = OrganizationFactory.create()
        self.user = UserFactory.create()

    def _save(self, identifier=None, identifier_field=None, ok=True):
        if identifier_field is not None:
            identifier = getattr(self.user, identifier_field)
        data = {'identifier': identifier}
        form = forms.AddOrganizationMemberForm(data, organization=self.org)
        num_roles_before = OrganizationRole.objects.count()
        if ok:
            form.save()
            assert form.is_valid() is True
            assert OrganizationRole.objects.filter(
                organization=self.org, user=self.user).count() == 1
        else:
            with raises(ValueError):
                form.save()
            assert form.is_valid() is False
            assert OrganizationRole.objects.count() == num_roles_before

    def test_add_with_username(self):
        self._save(identifier_field='username')

    def test_add_with_email(self):
        self._save(identifier_field='email')

    def test_add_non_existing_user(self):
        self._save(identifier='some-user', ok=False)

    def test_add_already_member_user(self):
        OrganizationRole.objects.create(
            organization=self.org, user=self.user)
        self._save(identifier_field='username', ok=False)


class EditOrganizationMemberFormTest(UserTestCase, TestCase):
    def test_edit_org_role(self):
        org = OrganizationFactory.create()
        user = UserFactory.create()
        current_user = UserFactory.create()
        prj_1 = ProjectFactory.create(organization=org)

        data = {'org_role': 'A',
                prj_1.id: 'A'}

        org_role = OrganizationRole.objects.create(organization=org, user=user)
        OrganizationRole.objects.create(
            organization=org, user=current_user, admin=True)
        form = forms.EditOrganizationMemberForm(data, org, user, current_user)

        form.save()
        org_role.refresh_from_db()

        assert form.is_valid() is True
        assert org_role.admin is True

    def test_edit_admin_role(self):
        # Should fail, since admins are not allowed to alter
        # their own permissions.
        org = OrganizationFactory.create()
        user = UserFactory.create()

        data = {'org_role': 'M'}

        org_role = OrganizationRole.objects.create(
            organization=org, user=user, admin=True)
        form = forms.EditOrganizationMemberForm(data, org, user, user)
        assert not form.is_valid()
        assert form.errors == {
            'org_role': ["Organization administrators cannot change their" +
                         " own role in the organization."]
        }
        org_role.refresh_from_db()
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

        form = forms.EditOrganizationMemberForm(data, org, user, user)

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


class ProjectAddDetailsTest(UserTestCase, TestCase):
    def setUp(self):
        super().setUp()
        self.org = OrganizationFactory.create()
        self.user = UserFactory.create()

        OrganizationRole.objects.create(
            organization=self.org, user=self.user, admin=True
        )
        self.data = {
            'organization': self.org.slug,
            'name': "Project Name",
            'description': "",
            'urls': '',
            'contacts-TOTAL_FORMS': 1,
            'contacts-INITIAL_FORMS': 0,
            'contacts-0-name': '',
            'contacts-0-email': '',
            'contacts-0-tel': ''
        }

    def test_add_new_project_with_restricted_name(self):
        invalid_names = ('add', 'ADD', 'Add', 'new', 'NEW', 'New')
        data = self.data.copy()
        data['name'] = random.choice(invalid_names)
        form = forms.ProjectAddDetails(data=data, user=self.user)
        assert not form.is_valid()
        assert form.errors == {
            'name': ["Project name cannot be “Add” or “New”."]
        }

    def test_add_new_project_with_duplicate_name(self):
        existing_project = ProjectFactory.create(organization=self.org)
        data = self.data.copy()
        data['name'] = existing_project.name
        form = forms.ProjectAddDetails(data=data, user=self.user)
        assert not form.is_valid()
        assert form.errors == {
            'name': [
                "Project with this name already exists in this organization."]
        }

    def test_add_new_project_with_duplicate_name_in_another_org(self):
        another_org = OrganizationFactory.create()
        existing_project = ProjectFactory.create(organization=another_org)
        data = self.data.copy()
        data['name'] = existing_project.name
        form = forms.ProjectAddDetails(data=data, user=self.user)
        assert form.is_valid()

    def test_add_new_project_with_semivalid_url(self):
        data = self.data.copy()
        data['url'] = 'cadasta.org'
        form = forms.ProjectAddDetails(data=data, user=self.user)
        assert form.is_valid()

    def test_add_new_project_with_invalid_url(self):
        data = self.data.copy()
        data['url'] = 'invalid url'
        form = forms.ProjectAddDetails(data=data, user=self.user)
        assert not form.is_valid()
        assert form.errors == {
            'url': ["Enter a valid URL."]
        }

    def test_add_new_project_with_archived_org(self):
        self.org.archived = True
        self.org.save()
        form = forms.ProjectAddDetails(user=self.user)
        choices = form.fields['organization'].choices
        assert len(choices) == 0

    def test_add_new_project_with_archived_org_with_superuser(self):
        self.org.archived = True
        self.org.save()
        su_role = Role.objects.get(name='superuser')
        self.user.assign_policies(su_role)
        assert self.user.has_perm('project.create', self.org)
        form = forms.ProjectAddDetails(user=self.user)
        choices = form.fields['organization'].choices
        assert len(choices) == 0

    def test_add_new_project_with_blank_org_choice(self):
        second_org = OrganizationFactory.create()
        OrganizationRole.objects.create(
            organization=second_org, user=self.user, admin=True
        )
        form = forms.ProjectAddDetails(user=self.user)
        choices = form.fields['organization'].choices
        assert len(choices) == 3
        assert choices[0] == ('', "Please select an organization")

    def test_add_new_project_without_blank_org_choice_with_chosen_org(self):
        second_org = OrganizationFactory.create()
        OrganizationRole.objects.create(
            organization=second_org, user=self.user, admin=True
        )
        form = forms.ProjectAddDetails(user=self.user, org_is_chosen=True)
        choices = form.fields['organization'].choices
        assert len(choices) == 2
        assert '' not in dict(choices)

    def test_add_new_project_without_blank_org_choice_with_1_org(self):
        form = forms.ProjectAddDetails(user=self.user)
        choices = form.fields['organization'].choices
        assert len(choices) == 1
        assert choices[0] == (self.org.slug, self.org.name)


@pytest.mark.usefixtures('make_dirs')
class ProjectEditDetailsTest(UserTestCase, TestCase):
    def setUp(self):
        self.project = ProjectFactory.create()
        self.data = {
            'name': self.project.name,
            'description': self.project.description,
            'urls': '',
            'contacts-TOTAL_FORMS': 1,
            'contacts-INITIAL_FORMS': 0,
            'contacts-0-name': '',
            'contacts-0-email': '',
            'contacts-0-tel': ''
        }

    def _get_form(self, form_name):
        path = os.path.dirname(settings.BASE_DIR)

        storage = FakeS3Storage()
        file = open(
            path + '/questionnaires/tests/files/{}.xlsx'.format(form_name),
            'rb'
        ).read()
        form = storage.save('xls-forms/{}.xlsx'.format(form_name), file)
        return form

    def test_add_new_questionnaire(self):
        project = ProjectFactory.create()
        data = {
            'name': 'New name',
            'questionnaire': self._get_form('xls-form'),
            'original_file': 'original.xls',
            'access': project.access,
            'contacts-TOTAL_FORMS': 1,
            'contacts-INITIAL_FORMS': 0,
            'contacts-0-name': '',
            'contacts-0-email': '',
            'contacts-0-tel': ''
        }

        form = forms.ProjectEditDetails(instance=project, data=data)
        form.save()

        project.refresh_from_db()
        assert project.name == data['name']
        questionnaire = project.questionnaires.get(
            id=project.current_questionnaire)
        assert questionnaire.xls_form.url == data['questionnaire']
        assert questionnaire.original_file == data['original_file']

    def test_add_invalid_questionnaire(self):
        project = ProjectFactory.create()
        data = {
            'name': 'New name',
            'questionnaire': self._get_form('xls-form-invalid'),
            'access': project.access,
            'contacts-TOTAL_FORMS': 1,
            'contacts-INITIAL_FORMS': 0,
            'contacts-0-name': '',
            'contacts-0-email': '',
            'contacts-0-tel': ''
        }

        form = forms.ProjectEditDetails(instance=project, data=data)
        with raises(InvalidXLSForm):
            form.save()

        project.refresh_from_db()
        assert project.name != data['name']
        assert project.current_questionnaire is None

    def test_replace_questionnaire(self):
        project = ProjectFactory.create()
        questionnaire = QuestionnaireFactory.create(
            project=project,
            xls_form=self._get_form('xls-form'))
        data = {
            'name': 'New name',
            'questionnaire': self._get_form('xls-form-copy'),
            'access': project.access,
            'contacts-TOTAL_FORMS': 1,
            'contacts-INITIAL_FORMS': 0,
            'contacts-0-name': '',
            'contacts-0-email': '',
            'contacts-0-tel': ''
        }

        form = forms.ProjectEditDetails(
            instance=project,
            data=data,
            initial={'questionnaire': questionnaire.xls_form.url})
        form.save()

        project.refresh_from_db()
        assert project.name == data['name']
        assert (project.questionnaires.get(
                    id=project.current_questionnaire
                ).xls_form.url == data['questionnaire'])

    def test_delete_questionnaire(self):
        project = ProjectFactory.create()
        questionnaire = QuestionnaireFactory.create(
            project=project,
            xls_form=self._get_form('xls-form'))
        data = {
            'name': 'New name',
            'questionnaire': '',
            'access': project.access,
            'contacts-TOTAL_FORMS': 1,
            'contacts-INITIAL_FORMS': 0,
            'contacts-0-name': '',
            'contacts-0-email': '',
            'contacts-0-tel': ''
        }

        form = forms.ProjectEditDetails(
            instance=project,
            data=data,
            initial={'questionnaire': questionnaire.xls_form.url})
        form.save()

        project.refresh_from_db()
        assert project.name == data['name']
        assert not project.current_questionnaire

    def test_update_project_with_restricted_name(self):
        invalid_names = ('add', 'ADD', 'Add', 'new', 'NEW', 'New')
        data = self.data.copy()
        data['name'] = random.choice(invalid_names)
        form = forms.ProjectEditDetails(instance=self.project, data=data)
        assert not form.is_valid()
        assert form.errors == {
            'name': ["Project name cannot be “Add” or “New”."]
        }

    def test_update_project_with_duplicate_name(self):
        another_project = ProjectFactory.create(
            organization=self.project.organization)
        data = self.data.copy()
        data['name'] = another_project.name
        form = forms.ProjectEditDetails(instance=self.project, data=data)
        assert not form.is_valid()
        assert form.errors == {
            'name': [
                "Project with this name already exists in this organization."]
        }

    def test_update_project_with_semivalid_url(self):
        data = self.data.copy()
        data['urls'] = 'cadasta.org'
        form = forms.ProjectEditDetails(instance=self.project, data=data)
        assert form.is_valid()
        project = form.save()
        assert project.urls == ['http://cadasta.org']

    def test_update_project_with_invalid_url(self):
        data = self.data.copy()
        data['urls'] = 'invalid url'
        form = forms.ProjectEditDetails(instance=self.project, data=data)
        assert not form.is_valid()
        assert form.errors == {
            'urls': ["Enter a valid URL."]
        }


class UpdateProjectRolesTest(UserTestCase, TestCase):
    def setUp(self):
        super().setUp()
        self.project = ProjectFactory.create()
        self.user = UserFactory.create()

    def test_create_new_role(self):
        """New ProjectRole instance should be created when role != Pb"""
        forms.create_update_or_delete_project_role(
            self.project.id, self.user, 'PM')

        assert ProjectRole.objects.count() == 1
        assert ProjectRole.objects.first().role == 'PM'

    def test_do_not_create_new_role_for_public_user(self):
        """No ProjectRole instance should be created when role == Pb"""
        forms.create_update_or_delete_project_role(
            self.project.id, self.user, 'Pb')

        assert ProjectRole.objects.count() == 0

    def test_update_existing_role(self):
        ProjectRole.objects.create(
            project=self.project,
            user=self.user,
            role='DC')
        forms.create_update_or_delete_project_role(
            self.project.id, self.user, 'PM')

        role = ProjectRole.objects.get(project=self.project, user=self.user)
        assert role.role == 'PM'

    def test_delete_existing_role(self):
        """If role is updated to Pb (public user) the Project Role instance
           should be deleted"""
        ProjectRole.objects.create(
            project=self.project,
            user=self.user,
            role='DC')
        forms.create_update_or_delete_project_role(
            self.project.id, self.user, 'Pb')
        assert ProjectRole.objects.count() == 0


class ProjectEditPermissionsTest(UserTestCase, TestCase):
    def setUp(self):
        super().setUp()
        self.project = ProjectFactory.create()

        self.super_user = UserFactory.create()
        OrganizationRole.objects.create(user=self.super_user,
                                        organization=self.project.organization,
                                        admin=False)
        su_role = Role.objects.get(name='superuser')
        self.super_user.assign_policies(su_role)

        self.org_admin = UserFactory.create()
        OrganizationRole.objects.create(user=self.org_admin,
                                        organization=self.project.organization,
                                        admin=True)
        self.project_user_1 = UserFactory.create()
        OrganizationRole.objects.create(user=self.project_user_1,
                                        organization=self.project.organization,
                                        admin=False)
        ProjectRole.objects.create(user=self.project_user_1,
                                   project=self.project,
                                   role='DC')
        self.project_user_2 = UserFactory.create()
        OrganizationRole.objects.create(user=self.project_user_2,
                                        organization=self.project.organization,
                                        admin=False)

    def test_init(self):
        form = forms.ProjectEditPermissions(instance=self.project)
        assert len(form.fields) == 4

        for k, field in form.fields.items():
            if field.user == self.project_user_2:
                assert field.initial == 'Pb'
            elif field.user == self.project_user_1:
                assert field.initial == 'DC'
            elif field.user == self.org_admin:
                assert field.initial == 'A'
            elif field.user == self.super_user:
                assert field.initial == 'A'

    def test_save(self):
        data = {
            self.project_user_1.username: 'PM',
            self.project_user_2.username: 'DC'
        }
        form = forms.ProjectEditPermissions(instance=self.project, data=data)
        form.save()

        role_1 = ProjectRole.objects.get(
            project=self.project,
            user=self.project_user_1
        )
        assert role_1.role == 'PM'

        role_2 = ProjectRole.objects.get(
            project=self.project,
            user=self.project_user_2
        )
        assert role_2.role == 'DC'


class ContactsFormTest(UserTestCase, TestCase):
    def test_as_table(self):
        form = forms.ContactsForm(prefix='c')
        html = form.as_table()

        expected = (
            '<tr><td><input id="id_c-name" name="c-name" type="text" /></td>\n'
            '<td><input id="id_c-email" name="c-email" type="email" /></td>\n'
            '<td><input id="id_c-tel" name="c-tel" type="text" />'
            '<input id="id_c-remove" name="c-remove" type="hidden" /></td>'
            '<td><a data-prefix="c" '
            'class="close remove-contact" href="#">'
            '<span aria-hidden="true">&times;</span></a></td></tr>\n'
        )
        assert expected == html

    def test_as_table_with_no_name_error(self):
        data = {
            'c-name': '',
            'c-email': 'john@beatles.uk',
        }
        form = forms.ContactsForm(data=data, prefix='c')
        html = form.as_table()

        expected = (
            '<tr class="contacts-error  error-name">'
            '<td colspan="4"><ul class="errorlist nonfield"><li>'
            'Please provide a name.</li></ul></td></tr>\n'
            '<tr>\n'
            '<td><input id="id_c-name" name="c-name" type="text" /></td>\n'
            '<td><input id="id_c-email" name="c-email" type="email" '
            'value="john@beatles.uk" /></td>\n'
            '<td><input id="id_c-tel" name="c-tel" type="text" />'
            '<input id="id_c-remove" name="c-remove" type="hidden" /></td>'
            '<td><a data-prefix="c" '
            'class="close remove-contact" href="#">'
            '<span aria-hidden="true">&times;</span></a></td></tr>\n'
        )
        assert expected == html

    def test_as_table_with_invalid_email_error(self):
        data = {
            'c-name': 'John',
            'c-email': 'invalid email',
        }
        form = forms.ContactsForm(data=data, prefix='c')
        html = form.as_table()

        expected = (
            '<tr class="contacts-error  error-email">'
            '<td colspan="4"><ul class="errorlist nonfield"><li>'
            'The provided email address is invalid.</li></ul></td></tr>\n'
            '<tr>\n'
            '<td><input id="id_c-name" name="c-name" type="text" '
            'value="John" /></td>\n'
            '<td><input id="id_c-email" name="c-email" type="email" '
            'value="invalid email" /></td>\n'
            '<td><input id="id_c-tel" name="c-tel" type="text" />'
            '<input id="id_c-remove" name="c-remove" type="hidden" /></td>'
            '<td><a data-prefix="c" '
            'class="close remove-contact" href="#">'
            '<span aria-hidden="true">&times;</span></a></td></tr>\n'
        )
        assert expected == html

    def test_as_table_with_no_name_and_invalid_email_error(self):
        data = {
            'c-name': '',
            'c-email': 'invalid email',
        }
        form = forms.ContactsForm(data=data, prefix='c')
        html = form.as_table()

        expected = (
            '<tr class="contacts-error  error-name error-email">'
            '<td colspan="4"><ul class="errorlist nonfield"><li>'
            'Please provide a name. '
            'The provided email address is invalid.</li></ul></td></tr>\n'
            '<tr>\n'
            '<td><input id="id_c-name" name="c-name" type="text" /></td>\n'
            '<td><input id="id_c-email" name="c-email" type="email" '
            'value="invalid email" /></td>\n'
            '<td><input id="id_c-tel" name="c-tel" type="text" />'
            '<input id="id_c-remove" name="c-remove" type="hidden" /></td>'
            '<td><a data-prefix="c" '
            'class="close remove-contact" href="#">'
            '<span aria-hidden="true">&times;</span></a></td></tr>\n'
        )
        assert expected == html

    def test_as_table_with_missing_email_or_phone_error(self):
        data = {
            'c-name': 'John',
        }
        form = forms.ContactsForm(data=data, prefix='c')
        html = form.as_table()

        expected = (
            '<tr class="contacts-error  error-email error-phone">'
            '<td colspan="4"><ul class="errorlist nonfield"><li>'
            'Please provide either an email address or a phone number.'
            '</li></ul></td></tr>\n'
            '<tr>\n'
            '<td><input id="id_c-name" name="c-name" type="text" '
            'value="John" /></td>\n'
            '<td><input id="id_c-email" name="c-email" type="email" /></td>\n'
            '<td><input id="id_c-tel" name="c-tel" type="text" />'
            '<input id="id_c-remove" name="c-remove" type="hidden" /></td>'
            '<td><a data-prefix="c" '
            'class="close remove-contact" href="#">'
            '<span aria-hidden="true">&times;</span></a></td></tr>\n'
        )
        assert expected == html

    def test_clean_string(self):
        form = forms.ContactsForm()
        assert form.clean_string('') is None
        assert form.clean_string('somthing') == 'somthing'

    def test_clean_email(self):
        data = {
            'contacts-name': 'John',
            'contacts-email': 'john@beatles.uk'
        }
        form = forms.ContactsForm(data=data, prefix='contacts')
        form.full_clean()
        assert form.clean_email() == data['contacts-email']

    def test_clean_email_empty_string(self):
        data = {
            'contacts-name': 'John',
            'contacts-email': '',
            'contacts-tel': '555-555'
        }
        form = forms.ContactsForm(data=data, prefix='contacts')
        form.full_clean()
        assert form.clean_email() is None

    def test_clean_tel(self):
        data = {
            'contacts-name': 'John',
            'contacts-tel': '555-5555'
        }
        form = forms.ContactsForm(data=data, prefix='contacts')
        form.full_clean()
        assert form.clean_tel() == data['contacts-tel']

    def test_clean_tel_empty_string(self):
        data = {
            'contacts-name': 'John',
            'contacts-email': 'john@beatles.uk',
            'contacts-tel': ''
        }
        form = forms.ContactsForm(data=data, prefix='contacts')
        form.full_clean()
        assert form.clean_tel() is None

    def test_full_clean(self):
        data = {
            'contacts-name': 'John',
            'contacts-email': 'john@beatles.uk'
        }
        form = forms.ContactsForm(data=data, prefix='contacts')
        form.full_clean()
        assert form.cleaned_data == {
            'name': 'John',
            'email': 'john@beatles.uk',
            'tel': None,
            'remove': False
        }

    def test_full_clean_remove(self):
        data = {
            'contacts-name': 'John',
            'contacts-email': 'john@beatles.uk',
            'contacts-remove': 'on'
        }
        form = forms.ContactsForm(data=data, prefix='contacts')
        form.full_clean()
        assert form.cleaned_data == {'remove': True}
        assert isinstance(form._errors, ErrorDict)

    def test_validate_valid_form_with_email(self):
        data = {
            'contacts-name': 'John',
            'contacts-email': 'john@beatles.uk',
        }
        form = forms.ContactsForm(data=data, prefix='contacts')
        assert form.is_valid() is True

    def test_validate_valid_form_with_tel(self):
        data = {
            'contacts-name': 'John',
            'contacts-email': '',
            'contacts-tel': '555-555'
        }
        form = forms.ContactsForm(data=data, prefix='contacts')
        assert form.is_valid() is True

    def test_validate_invalid_form_missing_name_invalid_email(self):
        data = {
            'contacts-name': '',
            'contacts-email': 'invalid',
            'contacts-tel': ''
        }
        form = forms.ContactsForm(data=data, prefix='contacts')
        assert form.is_valid() is False
        assert form.errors['name']
        assert form.errors['email']
        html = form.as_table()
        assert 'error-name' in html
        assert 'error-email' in html

    def test_validate_invalid_form_missing_contact_data(self):
        data = {
            'contacts-name': 'John',
            'contacts-email': '',
            'contacts-tel': ''
        }
        form = forms.ContactsForm(data=data, prefix='contacts')
        assert form.is_valid() is False
        assert ("Please provide either an email address or a phone number." in
                form.errors['__all__'])
        html = form.as_table()
        assert 'error-email' in html
        assert 'error-phone' in html


@pytest.mark.usefixtures('make_dirs')
@pytest.mark.usefixtures('clear_temp')
class DownloadFormTest(UserTestCase, TestCase):
    def test_init(self):
        ensure_dirs()
        user = UserFactory.build()
        project = ProjectFactory.build()
        form = forms.DownloadForm(project, user)
        assert form.project == project
        assert form.user == user

    def test_get_shape_download(self):
        ensure_dirs()
        data = {'type': 'shp'}
        user = UserFactory.create()
        project = ProjectFactory.create()
        form = forms.DownloadForm(project, user, data=data)
        assert form.is_valid() is True
        path, mime = form.get_file()
        assert '{}-{}'.format(project.id, user.id) in path
        assert (mime == 'application/zip')

        with ZipFile(path, 'r') as testzip:
            assert len(testzip.namelist()) == 16
            assert project.slug + '-point.dbf' in testzip.namelist()
            assert project.slug + '-point.prj' in testzip.namelist()
            assert project.slug + '-point.shp' in testzip.namelist()
            assert project.slug + '-point.shx' in testzip.namelist()
            assert project.slug + '-line.dbf' in testzip.namelist()
            assert project.slug + '-line.prj' in testzip.namelist()
            assert project.slug + '-line.shp' in testzip.namelist()
            assert project.slug + '-line.shx' in testzip.namelist()
            assert project.slug + '-polygon.dbf' in testzip.namelist()
            assert project.slug + '-polygon.prj' in testzip.namelist()
            assert project.slug + '-polygon.shp' in testzip.namelist()
            assert project.slug + '-polygon.shx' in testzip.namelist()
            assert 'relationships.csv' in testzip.namelist()
            assert 'parties.csv' in testzip.namelist()
            assert 'locations.csv' in testzip.namelist()
            assert 'README.txt' in testzip.namelist()

    def test_get_xls_download(self):
        ensure_dirs()
        data = {'type': 'xls'}
        user = UserFactory.create()
        project = ProjectFactory.create()
        form = forms.DownloadForm(project, user, data=data)
        assert form.is_valid() is True
        path, mime = form.get_file()
        assert '{}-{}'.format(project.id, user.id) in path
        assert (mime == 'application/vnd.openxmlformats-officedocument.'
                        'spreadsheetml.sheet')

    def test_get_resources_download(self):
        ensure_dirs()
        data = {'type': 'res'}
        user = UserFactory.create()
        project = ProjectFactory.create()
        form = forms.DownloadForm(project, user, data=data)
        assert form.is_valid() is True
        path, mime = form.get_file()
        assert '{}-{}'.format(project.id, user.id) in path
        assert mime == 'application/zip'

    def test_get_all_download(self):
        ensure_dirs()
        data = {'type': 'all'}
        user = UserFactory.create()
        project = ProjectFactory.create()
        res = ResourceFactory.create(project=project)

        form = forms.DownloadForm(project, user, data=data)
        assert form.is_valid() is True
        path, mime = form.get_file()
        assert '{}-{}'.format(project.id, user.id) in path
        assert mime == 'application/zip'

        with ZipFile(path, 'r') as testzip:
            assert len(testzip.namelist()) == 4
            assert res.original_file in testzip.namelist()
            assert 'resources.xlsx' in testzip.namelist()
            assert 'data.xlsx' in testzip.namelist()
            assert 'data-shp.zip' in testzip.namelist()
