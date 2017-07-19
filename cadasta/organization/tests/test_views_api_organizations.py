
from django.test import TestCase
from django.contrib.auth.models import Group
from rest_framework.exceptions import PermissionDenied
from skivvy import APITestCase

from core.tests.utils.cases import UserTestCase
from accounts.tests.factories import UserFactory
from .factories import OrganizationFactory, ProjectFactory
from ..models import Organization, OrganizationRole
from ..views import api


class OrganizationListAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.OrganizationList

    def setup_models(self):
        self.user = UserFactory.create()

    def test_full_list(self):
        """Return all organizations."""
        OrganizationFactory.create_batch(2)
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert len(response.content['results']) == 2
        assert 'users' not in response.content['results'][0]

    def test_full_list_based_on_org_member_role(self):
        OrganizationFactory.create_batch(2)
        org1 = OrganizationFactory.create(access='private')
        org2 = OrganizationFactory.create(archived=True)
        om = Group.objects.get(name='OrgMember')
        OrganizationRole.objects.create(
            organization=org1, user=self.user, group=om)
        OrganizationRole.objects.create(
            organization=org2, user=self.user, group=om)
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert len(response.content['results']) == 3
        assert 'users' not in response.content['results'][0]

    def test_full_list_based_on_org_admin_role(self):
        OrganizationFactory.create_batch(2)
        org2 = OrganizationFactory.create(archived=True)
        oa = Group.objects.get(name='OrgAdmin')
        OrganizationRole.objects.create(
            organization=org2, user=self.user, group=oa)
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert len(response.content['results']) == 3
        assert 'users' not in response.content['results'][0]

    def test_full_list_with_unauthorized_user(self):
        """Return all organizations."""
        OrganizationFactory.create_batch(2)
        response = self.request()
        assert response.status_code == 200
        assert len(response.content['results']) == 2
        assert 'users' not in response.content['results'][0]

    def test_filter_active(self):
        """Return only one archived organization."""
        org = OrganizationFactory.create(archived=True)
        OrganizationFactory.create(archived=False)
        oa = Group.objects.get(name='OrgAdmin')
        OrganizationRole.objects.create(organization=org,
                                        user=self.user,
                                        group=oa)
        response = self.request(user=self.user, get_data={'archived': True})
        assert response.status_code == 200
        assert len(response.content['results']) == 1
        assert response.content['results'][0]['archived'] is True

    def test_search_filter(self):
        """Return only two matching organizations."""
        OrganizationFactory.create_from_kwargs([
            {'name': 'A Match'},
            {'description': 'something that matches'},
            {'name': 'Excluded'}
        ])
        response = self.request(user=self.user, get_data={'search': 'match'})
        assert response.status_code == 200
        assert len(response.content['results']) == 2
        assert not any([org['name'] == 'Excluded' for org in
                        response.content['results']])

    def test_ordering(self):
        OrganizationFactory.create_from_kwargs([
            {'name': 'A'}, {'name': 'C'}, {'name': 'B'}
        ])
        response = self.request(user=self.user,
                                get_data={'ordering': 'name'})
        assert response.status_code == 200
        assert len(response.content['results']) == 3
        names = [org['name'] for org in response.content['results']]
        assert(names == sorted(names))

    def test_reverse_ordering(self):
        OrganizationFactory.create_from_kwargs([
            {'name': 'A'}, {'name': 'C'}, {'name': 'B'}
        ])
        response = self.request(user=self.user,
                                get_data={'ordering': '-name'})
        assert response.status_code == 200
        assert len(response.content['results']) == 3
        names = [org['name'] for org in response.content['results']]
        assert(names == sorted(names, reverse=True))


class OrganizationCreateAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.OrganizationList

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()

    def test_create_valid_organization(self):
        data = {'name': 'Org Name', 'description': 'Org description'}
        response = self.request(method='POST', user=self.user, post_data=data)
        assert response.status_code == 201
        assert Organization.objects.count() == 1
        assert OrganizationRole.objects.get(
            organization_id=response.content['id'],
            user=self.user).admin is True

    def test_create_invalid_organization(self):
        data = {'description': 'Org description'}
        response = self.request(method='POST', user=self.user, post_data=data)
        assert response.status_code == 400
        assert Organization.objects.count() == 0
        assert response.content['name'][0] == 'This field is required.'

    def test_create_with_anonymous_user(self):
        response = self.request(method='POST', post_data={'name': 'Org Name'})
        assert response.status_code == 401
        assert (response.content['detail'] ==
                'Authentication credentials were not provided.')
        assert Organization.objects.count() == 0


class OrganizationDetailAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.OrganizationDetail
    url_kwargs = {'organization': 'org'}

    def setup_models(self):
        self.user = UserFactory.create()
        self.org = OrganizationFactory.create(name='Org', slug='org')
        self.project = ProjectFactory.create(organization=self.org)
        self.org_admin = Group.objects.get(name='OrgAdmin')
        self.org_member = Group.objects.get(name='OrgMember')

    def test_get_organization_with_anonymous_user(self):
        response = self.request()
        assert response.status_code == 200
        assert response.content['id'] == self.org.id
        assert 'users' not in response.content

    def test_get_organization_with_unauthorized_user(self):
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content['id'] == self.org.id
        assert 'users' not in response.content

    def test_get_organization_with_authorized_user(self):
        OrganizationRole.objects.create(
            organization=self.org, user=self.user, group=self.org_admin)
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content['id'] == self.org.id
        assert 'users' in response.content

    def test_get_organization_that_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'organization': 'someorg'})
        assert response.status_code == 404
        assert response.content['detail'] == "Organization not found."

    def test_get_archived_organization_with_authorized_user(self):
        OrganizationRole.objects.create(
            organization=self.org, user=self.user, group=self.org_admin)
        self.org.archived = True
        self.org.save()
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content['id'] == self.org.id
        assert 'users' in response.content

    def test_get_archived_organization_with_anonymous_user(self):
        self.org.archived = True
        self.org.save()
        response = self.request()
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_valid_update(self):
        OrganizationRole.objects.create(
            organization=self.org, user=self.user, group=self.org_admin)
        data = {'name': 'Org Name'}
        response = self.request(method='PATCH', user=self.user, post_data=data)
        assert response.status_code == 200
        self.org.refresh_from_db()
        assert self.org.name == data.get('name')

    def test_PATCH_with_anonymous_user(self):
        data = {'name': 'Org Name'}
        response = self.request(method='PATCH', post_data=data)
        assert response.status_code == 401
        assert (response.content['detail'] ==
                'Authentication credentials were not provided.')
        self.org.refresh_from_db()
        assert self.org.name == 'Org'

    def test_PATCH_with_unauthorized_user(self):
        user = UserFactory.create()
        data = {'name': 'Org Name'}
        response = self.request(method='PATCH', post_data=data, user=user)
        assert response.status_code == 403
        self.org.refresh_from_db()
        assert self.org.name == 'Org'

    def test_PUT_with_anonymous_user(self):
        data = {'name': 'Org Name'}
        response = self.request(method='PUT', post_data=data)
        assert response.status_code == 401
        assert (response.content['detail'] ==
                'Authentication credentials were not provided.')
        self.org.refresh_from_db()
        assert self.org.name == 'Org'

    def test_PUT_with_unauthorized_user(self):
        user = UserFactory.create()
        data = {'name': 'Org Name'}
        response = self.request(method='PUT', post_data=data, user=user)
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail
        self.org.refresh_from_db()
        assert self.org.name == 'Org'

    def test_update_with_archived_org(self):
        self.org.archived = True
        self.org.save()
        data = {'name': 'Org Name'}
        response = self.request(method='PATCH', user=self.user, post_data=data)
        assert response.status_code == 403
        self.org.refresh_from_db()
        assert self.org.name == 'Org'

    def test_invalid_update(self):
        OrganizationRole.objects.create(
            organization=self.org, user=self.user, group=self.org_admin)
        data = {'name': ''}
        response = self.request(method='PATCH', post_data=data, user=self.user)
        self.org.refresh_from_db()
        assert response.status_code == 400
        assert self.org.name == 'Org'
        assert response.content['name'][0] == 'This field may not be blank.'

    def test_archive(self):
        OrganizationRole.objects.create(
            organization=self.org, user=self.user, group=self.org_admin)
        data = {'archived': True}
        response = self.request(method='PATCH', post_data=data, user=self.user)
        assert response.status_code == 200
        self.org.refresh_from_db()
        self.project.refresh_from_db()
        assert self.org.archived is True
        assert self.project.archived is True
        # add test for archiving project, and updating archived org.

    def test_archive_with_unauthorized_user(self):
        data = {'archived': True}
        response = self.request(method='PATCH', user=self.user, post_data=data)
        assert response.status_code == 403
        self.org.refresh_from_db()
        assert self.org.archived is False

    def test_unarchive(self):
        OrganizationRole.objects.create(
            organization=self.org, user=self.user, group=self.org_admin)
        data = {'archived': False}
        response = self.request(method='PATCH', post_data=data, user=self.user)
        assert response.status_code == 200
        self.org.refresh_from_db()
        assert self.org.archived is False
        assert self.project.archived is False

    def test_unarchive_with_unauthorized_user(self):
        self.org.archived = True
        self.org.save()
        data = {'archived': False}
        response = self.request(method='PATCH', user=self.user, post_data=data)
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail
        self.org.refresh_from_db()
        assert self.org.archived is True


class OrganizationUsersAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.OrganizationUsers
    url_kwargs = {'organization': 'org'}

    def setup_models(self):
        self.user = UserFactory.create()
        org_users = UserFactory.create_batch(2)
        self.org = OrganizationFactory.create(
            slug='org', add_users=org_users)
        oa = Group.objects.get(name='OrgAdmin')
        OrganizationRole.objects.create(
            organization=self.org, user=self.user, group=oa)

    def create_normal_org(self):
        org_users = UserFactory.create_batch(2)
        return OrganizationFactory.create(add_users=org_users)

    def test_get_users(self):
        other_user = UserFactory.create()
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert len(response.content['results']) == 3
        assert (other_user.username not in
                [u['username'] for u in response.content['results']])

    def test_get_users_with_unauthorized_user(self):
        response = self.request()
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_add_user(self):
        new_user = UserFactory.create()
        response = self.request(user=self.user, method='POST',
                                post_data={'username': new_user.username})
        assert response.status_code == 201
        assert self.org.users.count() == 4
        r = OrganizationRole.objects.get(organization=self.org, user=new_user)
        assert not r.admin

    def test_add_user_when_role_exists(self):
        new_user = UserFactory.create()
        pu = Group.objects.get(name='ProjectMember')
        OrganizationRole.objects.create(
            user=new_user, group=pu, organization=self.org)
        response = self.request(user=self.user, method='POST',
                                post_data={'username': new_user.username})
        assert response.status_code == 400

    def test_add_user_with_anonymous_user(self):
        new_user = UserFactory.create()
        response = self.request(method='POST',
                                post_data={'username': new_user.username})
        assert response.status_code == 401
        assert (response.content['detail'] ==
                'Authentication credentials were not provided.')
        assert self.org.users.count() == 3

    def test_add_user_with_superuser(self):
        superuser = UserFactory.create(is_superuser=True)
        new_user = UserFactory.create()
        response = self.request(method='POST',
                                user=superuser,
                                post_data={'username': new_user.username})
        assert response.status_code == 201
        assert self.org.users.count() == 4
        r = OrganizationRole.objects.get(organization=self.org, user=new_user)
        assert not r.admin

    def test_add_user_that_does_not_exist(self):
        response = self.request(method='POST', user=self.user,
                                post_data={'username': 'some_username'})
        assert response.status_code == 400
        assert self.org.users.count() == 3
        assert ("User with username or email some_username does not exist"
                in response.content['username'])

    def test_add_user_to_organization_that_does_not_exist(self):
        new_user = UserFactory.create()
        response = self.request(method='POST', user=self.user,
                                url_kwargs={'organization': 'some-org'},
                                post_data={'username': new_user.username})
        assert response.status_code == 404
        assert response.content['detail'] == "Organization not found."

    def test_add_user_to_archived_organization(self):
        new_user = UserFactory.create()
        self.org.archived = True
        self.org.save()
        response = self.request(user=self.user, method='POST',
                                post_data={'username': new_user.username})
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail
        assert self.org.users.count() == 3


class OrganizationUsersDetailAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.OrganizationUsersDetail

    def setup_models(self):
        self.user = UserFactory.create()
        self.org_user = UserFactory.create()
        self.org = OrganizationFactory.create(add_users=[self.org_user])
        self.oa = Group.objects.get(name='OrgAdmin')
        self.om = Group.objects.get(name='OrgMember')

    def setup_url_kwargs(self):
        return {
            'organization': self.org.slug,
            'username': self.org_user.username
        }

    def test_get_user(self):
        OrganizationRole.objects.create(organization=self.org,
                                        user=self.user,
                                        group=self.oa)
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content['username'] == self.org_user.username

    def test_update_user(self):
        OrganizationRole.objects.create(organization=self.org,
                                        user=self.user,
                                        group=self.oa)
        response = self.request(user=self.user,
                                method='PATCH',
                                post_data={'admin': 'true'})
        assert response.status_code == 200
        role = OrganizationRole.objects.get(organization=self.org,
                                            user=self.org_user)
        assert role.admin is True

    def test_PATCH_user_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user,
                                method='PATCH',
                                post_data={'admin': 'true'})
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail
        role = OrganizationRole.objects.get(organization=self.org,
                                            user=self.org_user)
        assert role.admin is False

    def test_PATCH_user_with_anonymous_user(self):
        response = self.request(method='PATCH',
                                post_data={'admin': 'true'})
        assert response.status_code == 401
        assert (response.content['detail'] ==
                'Authentication credentials were not provided.')
        role = OrganizationRole.objects.get(organization=self.org,
                                            user=self.org_user)
        assert role.admin is False

    def test_PUT_user_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user,
                                method='PUT',
                                post_data={'admin': 'true'})
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail
        role = OrganizationRole.objects.get(organization=self.org,
                                            user=self.org_user)
        assert role.admin is False

    def test_PUT_user_with_anonymous_user(self):
        response = self.request(method='PUT',
                                post_data={'admin': 'true'})
        assert response.status_code == 401
        assert (response.content['detail'] ==
                'Authentication credentials were not provided.')
        role = OrganizationRole.objects.get(organization=self.org,
                                            user=self.org_user)
        assert role.admin is False

    def test_update_admin_user(self):
        OrganizationRole.objects.create(organization=self.org,
                                        user=self.user,
                                        group=self.oa)
        response = self.request(user=self.user,
                                method='PATCH',
                                post_data={'admin': 'false'},
                                url_kwargs={'username': self.user.username})

        assert response.status_code == 400
        errs = response.content['admin']
        assert errs[0] == ("Organization administrators cannot"
                           " change their own permissions within"
                           " the organization")
        role = OrganizationRole.objects.get(organization=self.org,
                                            user=self.user)
        assert role.admin is True

    def test_update_user_in_archived_organization(self):
        self.org.archived = True
        self.org.save()
        response = self.request(user=self.user,
                                method='PATCH',
                                post_data={'admin': 'true'})
        assert response.status_code == 403
        role = OrganizationRole.objects.get(organization=self.org,
                                            user=self.org_user)
        assert role.admin is False

    def test_remove_user(self):
        OrganizationRole.objects.create(organization=self.org,
                                        group=self.oa,
                                        user=self.user)
        response = self.request(
            user=self.user,
            method='DELETE',
            url_kwargs={'username': self.org_user.username})
        assert response.status_code == 204
        assert self.org.users.count() == 1
        assert self.org_user not in self.org.users.all()

    def test_remove_admin_user(self):
        OrganizationRole.objects.create(organization=self.org,
                                        user=self.user,
                                        group=self.oa)
        response = self.request(
            user=self.user,
            method='DELETE',
            url_kwargs={'username': self.user.username})
        assert response.status_code == 403
        assert self.org.users.count() == 2
        assert self.user in self.org.users.all()

    def test_remove_with_anonymous_user(self):
        user_to_remove = UserFactory.create()
        OrganizationRole.objects.create(organization=self.org,
                                        group=self.om,
                                        user=user_to_remove)
        response = self.request(method='DELETE')
        assert response.status_code == 401
        assert (response.content['detail'] ==
                'Authentication credentials were not provided.')
        assert self.org.users.count() == 2

    def test_remove_user_that_does_not_exist(self):
        OrganizationRole.objects.create(organization=self.org,
                                        user=self.user,
                                        group=self.oa)
        response = self.request(user=self.user,
                                method='DELETE',
                                url_kwargs={'username': 'us'})
        assert response.status_code == 404
        assert response.content['detail'] == "User not found."

    def test_remove_user_from_organization_that_does_not_exist(self):
        response = self.request(user=self.user,
                                method='DELETE',
                                url_kwargs={'organization': 'blah'})
        assert response.status_code == 404
        assert response.content['detail'] == "Organization not found."

    def test_remove_user_from_archived_organization(self):
        self.org.archived = True
        self.org.save()
        user_to_remove = UserFactory.create()
        OrganizationRole.objects.create(organization=self.org,
                                        group=self.om,
                                        user=user_to_remove)
        response = self.request(
            user=self.user,
            method='DELETE',
            url_kwargs={'username': user_to_remove.username})
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail
        assert self.org.users.count() == 2
