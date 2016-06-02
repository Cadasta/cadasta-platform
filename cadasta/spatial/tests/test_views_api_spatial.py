import json

from django.test import TestCase
from django.utils.translation import gettext as _
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.exceptions import PermissionDenied
from tutelary.models import Policy, assign_user_policies

from accounts.tests.factories import UserFactory
from organization.tests.factories import (ProjectFactory, OrganizationFactory,
                                          clause)
from organization.models import OrganizationRole
from .factories import SpatialUnitFactory
from ..models import SpatialUnit
from ..views import api


class SpatialUnitListTestCase(TestCase):
    def setUp(self):
        self.view = api.SpatialUnitList.as_view()

        clauses = {
            'clause': [
                {
                    'effect': 'allow',
                    'object': ['project/*/*'],
                    'action': ['project.*', 'spatial.*']
                }
            ]
        }

        policy = Policy.objects.create(
            name='test-policy',
            body=json.dumps(clauses))

        self.user = UserFactory.create()
        self.user.assign_policies(policy)

        restricted_clauses = {
            'clause': [
                clause('allow', ['project.list'], ['organization/*']),
                clause('allow', ['project.view'], ['project/*/*'])
            ]
        }
        restricted_policy = Policy.objects.create(
            name='restricted',
            body=json.dumps(restricted_clauses))
        self.restricted_user = UserFactory.create()
        assign_user_policies(self.restricted_user, restricted_policy)

    def _get(self, org, prj, user=None, query=None, status=None, length=None):
        if user is None:
            user = self.user
        url = '/v1/organizations/{org}/projects/{prj}/spatial/'
        if query is not None:
            url += '?' + query
        request = APIRequestFactory().get(url.format(org=org, prj=prj))
        force_authenticate(request, user=user)
        response = self.view(request, organization=org,
                             project_slug=prj).render()
        content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        if length is not None:
            assert len(content['features']) == length
        return content

    def _post(self, org, prj, data=None, user=None, status=None, count=None):
        if user is None:
            user = self.user
        if data is None:
            data = {
                "properties": {
                    "name": "Small world"
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [100, 0]
                }
            }
        url = '/v1/organizations/{org}/projects/{prj}/spatial/'
        request = APIRequestFactory().post(url.format(
            org=org, prj=prj), data=data, format='json')
        force_authenticate(request, user=user)
        response = api.SpatialUnitList.as_view()(
            request, organization=org, project_slug=prj
        ).render()
        content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        if count is not None:
            assert SpatialUnit.objects.count() == count
        return content

    def _test_objs(self, access='public'):
        organization = OrganizationFactory.create(slug='namati')
        project = ProjectFactory.create(slug='test-project',
                                        organization=organization,
                                        access=access)
        SpatialUnitFactory.create(name='Top of the world', project=project)
        SpatialUnitFactory.create(name='South Pole', project=project)
        SpatialUnitFactory.create(name='Center of the earth', project=project,
                                  type='RW')
        return organization


class SpatialUnitListAPITest(SpatialUnitListTestCase):
    def _test_list_private_spatial_unit(self, status=None, user=None,
                                        check_error=False, length=None,
                                        make_org_member=False,
                                        make_other_org_member=False):
        if user is None:
            user = self.user
        org = self._test_objs(access='private')
        if make_org_member:
            OrganizationRole.objects.create(organization=org, user=user)
        if make_other_org_member:
            other_org = OrganizationFactory.create()
            OrganizationRole.objects.create(organization=other_org, user=user)
        cont = self._get(org=org.slug, prj='test-project', user=user,
                         status=status, length=length)
        if check_error:
            assert cont['detail'] == PermissionDenied.default_detail

    def test_full_list(self):
        """
        It should return all spatial units for a project,
        but not other projects.
        """
        self._test_objs()
        su_other = SpatialUnitFactory.create()
        content = self._get('namati', 'test-project', status=200, length=3)
        assert su_other.name not in ([u['properties']['name']
                                     for u in content['features']])

    def test_full_list_with_unauthorized_user(self):
        self._test_objs()
        content = self._get('namati', 'test-project',
                            user=AnonymousUser(), status=403)
        assert content['detail'] == PermissionDenied.default_detail

    def test_list_private_spatial_units(self):
        self._test_list_private_spatial_unit(status=200, length=3)

    def test_list_private_spatial_units_without_permission(self):
        self._test_list_private_spatial_unit(
            user=self.restricted_user, status=403, check_error=True
        )

    def test_list_private_spatial_units_based_on_org_membership(self):
        self._test_list_private_spatial_unit(
            user=UserFactory.create(), status=200, length=3,
            make_org_member=True
        )

    def test_list_private_spatial_units_with_other_org_membership(self):
        self._test_list_private_spatial_unit(
            user=UserFactory.create(), status=403, check_error=True,
            make_other_org_member=True
        )

    def test_full_list_with_nonexistant_org(self):
        self._test_objs()
        content = self._get('evil-corp', 'test-project', status=404)
        assert content['detail'] == "Project not found."

    def test_full_list_with_nonexistant_project(self):
        self._test_objs()
        content = self._get('namati', 'world-domination',
                            status=404)
        assert content['detail'] == "Project not found."

    def test_search_filter(self):
        self._test_objs()
        content = self._get(org='namati', prj='test-project',
                            query='search=earth', status=200, length=1)

        assert all(
            su['properties']['name'] == 'Center of the earth' for
            su in content['features'])

    def test_ordering(self):
        self._test_objs()
        content = self._get(org='namati', prj='test-project',
                            query='ordering=name', status=200)
        names = [su['properties']['name'] for su in content['features']]
        assert names == sorted(names)

    def test_reverse_ordering(self):
        self._test_objs()
        content = self._get(org='namati', prj='test-project',
                            query='ordering=-name', status=200)
        names = [su['properties']['name'] for su in content['features']]
        assert names == sorted(names, reverse=True)

    def test_type_filter(self):
        self._test_objs()
        content = self._get(org='namati', prj='test-project',
                            query='type=RW', status=200, length=1)
        assert all(
            su['properties']['type'] == 'RW' for su in content['features'])


class SpatialUnitCreateAPITest(SpatialUnitListTestCase):
    def _test_create_private_spatial_unit(self, status=None, user=None,
                                          check_error=False, count=None,
                                          make_org_member=False,
                                          make_other_org_member=False):
        if user is None:
            user = self.user
        org = self._test_objs(access='private')
        if make_org_member:
            OrganizationRole.objects.create(organization=org, user=user)
        if make_other_org_member:
            other_org = OrganizationFactory.create()
            OrganizationRole.objects.create(organization=other_org, user=user)
        cont = self._post(org=org.slug, prj='test-project', user=user,
                          status=status, count=count)
        if check_error:
            assert cont['detail'] == PermissionDenied.default_detail

    def test_create_valid_spatial_unit(self):
        self._test_objs()
        self._post(org='namati', prj='test-project',
                   status=201, count=4)

    def test_create_invalid_spatial_unit(self):
        self._test_objs()
        invalid_data = {
            "geometry": {
                "type": "Point",
                "coordinates": [100, 0]
            }
        }
        content = self._post(org='namati', prj='test-project',
                             data=invalid_data, status=400, count=3)
        assert content['name'][0] == _('This field is required.')

    def test_create_spatial_unit_with_invalid_geometry(self):
        self._test_objs()
        cat_data = {
            "name": "Cat points!",
            "geometry": {
                "type": "Cats",
                "coordinates": [100, 0]
            }
        }
        content = self._post(org='namati', prj='test-project',
                             data=cat_data, status=400, count=3)
        assert content['geometry'][0] == _('Invalid format: string or unicode'
                                           ' input unrecognized as GeoJSON, '
                                           'WKT EWKT or HEXEWKB.')

    def test_create_spatial_unit_with_unauthorized_user(self):
        self._test_objs()
        content = self._post(org='namati', prj='test-project',
                             user=AnonymousUser(), status=403, count=3)
        assert content['detail'] == PermissionDenied.default_detail

    def test_create_private_spatial_unit(self):
        self._test_create_private_spatial_unit(status=201, count=4)

    def test_create_private_spatial_unit_without_permission(self):
        self._test_create_private_spatial_unit(
            user=self.restricted_user, status=403, check_error=True,
            count=3
        )

    def test_create_private_spatial_unit_based_on_org_membership(self):
        self._test_create_private_spatial_unit(
            user=UserFactory.create(), status=403, count=3,
            make_org_member=True
        )

    def test_create_private_spatial_unit_with_other_org_membership(self):
        self._test_create_private_spatial_unit(
            user=UserFactory.create(), status=403, check_error=True,
            make_other_org_member=True, count=3
        )

    def test_create_spatial_unit_with_nonexistent_org(self):
        self._test_objs()
        content = self._post(org='evil-corp', prj='test-project',
                             status=404, count=3)
        assert content['detail'] == "Project not found."

    def test_create_spatial_unit_with_nonexistent_project(self):
        self._test_objs()
        content = self._post(org='namati', prj='world-domination', status=404,
                             count=3)
        assert content['detail'] == "Project not found."


class SpatialUnitDetailTestCase(TestCase):
    def setUp(self):
        self.view = api.SpatialUnitDetail.as_view()

        clauses = {
            'clause': [
                {
                    'effect': 'allow',
                    'object': ['project/*/*/*'],
                    'action': ['project.*', 'spatial.*']
                }
            ]
        }
        policy = Policy.objects.create(
            name='test-policy',
            body=json.dumps(clauses))
        self.user = UserFactory.create()
        self.user.assign_policies(policy)

        restricted_clauses = {
            'clause': [
                clause('allow', ['project.list'], ['organization/*']),
                clause('allow', ['project.view'], ['project/*/*'])
            ]
        }
        restricted_policy = Policy.objects.create(
            name='restricted',
            body=json.dumps(restricted_clauses))
        self.restricted_user = UserFactory.create()
        assign_user_policies(self.restricted_user, restricted_policy)

    def _get(self, org, prj, su, user=None, status=None):
        if user is None:
            user = self.user
        url = '/v1/organizations/{org}/projects/{prj}/spatial/{su}/'
        request = APIRequestFactory().get(url.format(org=org, prj=prj, su=su))
        force_authenticate(request, user=user)
        response = self.view(request, organization=org,
                             project_slug=prj, spatial_id=su).render()
        content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        return content

    def _patch(self, org, prj, su, data, user=None, status=None):
        if user is None:
            user = self.user
        url = '/v1/organizations/{org}/projects/{prj}/spatial/{su}/'
        request = APIRequestFactory().patch(
            url.format(org=org, prj=prj, su=su.id), data, format='json'
        )
        force_authenticate(request, user=user)
        response = self.view(request, organization=org, project_slug=prj,
                             spatial_id=su.id).render()
        content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        su.refresh_from_db()
        return content

    def _delete(self, org, prj, su, user=None, status=None):
        if user is None:
            user = self.user
        url = '/v1/organizations/{org}/projects/{prj}/spatial/{su}/'
        request = APIRequestFactory().delete(
            url.format(org=org, prj=prj, su=su.id)
        )
        force_authenticate(request, user=user)
        response = self.view(request, organization=org, project_slug=prj,
                             spatial_id=su.id).render()
        if status is not None:
            assert response.status_code == status
        if response.content:
            content = json.loads(response.content.decode('utf-8'))
            return content

    def _test_objs(self, access='public'):
        organization = OrganizationFactory.create(slug='namati')
        project = ProjectFactory.create(slug='test-project',
                                        organization=organization,
                                        access=access)
        su = SpatialUnitFactory.create(project=project,
                                       name='Test Spatial Unit')
        return (su, organization)


class SpatialUnitDetailAPITest(SpatialUnitDetailTestCase):
    def _test_get_public_spatial_unit(self, user, status, org='namati',
                                      prj='test-project', check_ok=False,
                                      check_error=False, non_existent=False):
        su = self._test_objs()[0]
        su_id = su.id
        if non_existent and prj == 'test-project' and org == 'namati':
            su_id = 'notanid'
        content = self._get(org=org, prj=prj,
                            su=su_id, user=user, status=status)
        if check_ok:
            assert content['properties']['id'] == su.id
        if check_error:
            assert content['detail'] == PermissionDenied.default_detail
        if non_existent:
            if su_id == 'notanid':
                assert content['detail'] == _("SpatialUnit not found.")
            else:
                assert content['detail'] == _("Project not found.")

    def _test_get_private_spatial_unit(self, status=None, user=None,
                                       check_ok=False, check_error=False,
                                       make_org_member=False,
                                       make_other_org_member=False):
        if user is None:
            user = self.user
        su, org = self._test_objs(access='private')
        if make_org_member:
            OrganizationRole.objects.create(organization=org, user=user)
        if make_other_org_member:
            other_org = OrganizationFactory.create()
            OrganizationRole.objects.create(organization=other_org, user=user)
        cont = self._get(org='namati', prj='test-project', su=su.id, user=user,
                         status=status)
        if check_ok:
            assert cont['properties']['id'] == su.id
        if check_error:
            assert cont['detail'] == PermissionDenied.default_detail

    def test_get_public_spatial_unit_with_valid_user(self):
        self._test_get_public_spatial_unit(self.user, 200, check_ok=True)

    def test_get_public_spatial_unit_that_does_not_exist(self):
        self._test_get_public_spatial_unit(self.user, 404,
                                           non_existent=True)

    def test_get_spatial_unit_from_org_that_does_not_exist(self):
        self._test_get_public_spatial_unit(self.user, 404,
                                           org='evil-corp', non_existent=True)

    def test_get_spatial_unit_from_project_that_does_not_exist(self):
        self._test_get_public_spatial_unit(self.user, 404,
                                           prj='world-dom', non_existent=True)

    def test_get_public_spatial_unit_with_unauthorized_user(self):
        self._test_get_public_spatial_unit(
            AnonymousUser(), 403, check_error=True)

    def test_get_private_spatial_unit(self):
        self._test_get_private_spatial_unit(
            status=200, check_ok=True
        )

    def test_get_private_spatial_unit_with_unauthroized_user(self):
        self._test_get_private_spatial_unit(
            user=AnonymousUser(), status=403, check_error=True
        )

    def test_get_private_spatial_unit_without_permission(self):
        self._test_get_private_spatial_unit(
            user=self.restricted_user, status=403, check_error=True
        )

    def test_get_private_spatial_unit_based_on_org_membership(self):
        self._test_get_private_spatial_unit(
            user=UserFactory.create(), status=200, check_ok=True,
            make_org_member=True
        )

    def test_get_private_spatial_unit_with_other_org_membership(self):
        self._test_get_private_spatial_unit(
            user=UserFactory.create(), status=403, check_error=True,
            make_other_org_member=True
        )


class SpatialUnitUpdateAPITest(SpatialUnitDetailTestCase):
    def _test_patch_public_spatial_unit(self, data, status, user=None,
                                        org='namati', prj='test-project',
                                        su=None, check_ok=False,
                                        check_error=False, non_existent=False,
                                        field_error=False, no_change=False):
        valid_su = self._test_objs()[0]
        su = su or valid_su
        if user is None:
            user = self.user
        content = self._patch(org=org, prj=prj, su=su, user=user,
                              data=data, status=status)
        if check_ok:
            assert content['properties']['name'] == check_ok
        if check_error:
            assert content['detail'] == PermissionDenied.default_detail
        if non_existent:
            if su != valid_su:
                assert content['detail'] == _("SpatialUnit not found.")
            else:
                assert content['detail'] == _("Project not found.")
        if field_error:
            if field_error == 'geometry':
                assert content['geometry'][0] == _('Invalid format: string or'
                                                   ' unicode input'
                                                   ' unrecognized as GeoJSON, '
                                                   'WKT EWKT or HEXEWKB.')
            elif field_error == 'name':
                assert content['name'][0] == _('This field may not be blank.')
        if no_change:
            content = self._get(org='namati', prj='test-project',
                                su=valid_su.id)
            assert content['properties']['name'] == 'Test Spatial Unit'

    def _test_patch_private_spatial_unit(self, data, status=None, user=None,
                                         check_ok=False, check_error=False,
                                         no_change=False,
                                         make_org_member=False,
                                         make_org_admin=False,
                                         make_other_org_member=False):
        if user is None:
            user = self.user
        su, org = self._test_objs(access='private')
        if make_org_member:
            OrganizationRole.objects.create(organization=org, user=user)
        if make_org_admin:
            OrganizationRole.objects.create(organization=org, user=user,
                                            admin=True)
        if make_other_org_member:
            other_org = OrganizationFactory.create()
            OrganizationRole.objects.create(organization=other_org, user=user)
        cont = self._patch(org='namati', prj='test-project', su=su,
                           user=user, data=data, status=status)
        if check_ok:
            assert cont['properties']['name'] == su.name
        if check_error:
            assert cont['detail'] == PermissionDenied.default_detail
        if no_change:
            content = self._get(org='namati', prj='test-project',
                                su=su.id)
            assert content['properties']['name'] == 'Test Spatial Unit'

    def test_update_with_valid_data(self):
        data = {'name': 'Way Cooler Name'}
        self._test_patch_public_spatial_unit(data, 200,
                                             check_ok='Way Cooler Name')

    def test_update_with_nonexistent_org(self):
        data = {'name': 'Cave of Doom'}
        self._test_patch_public_spatial_unit(data, 404,
                                             org='evil-corp',
                                             non_existent=True,
                                             no_change=True)

    def test_update_with_nonexistent_project(self):
        data = {'name': 'Cave of Doom'}
        self._test_patch_public_spatial_unit(data, 404,
                                             prj='world-domination',
                                             non_existent=True,
                                             no_change=True)

    def test_update_with_nonexistent_spatial_unit(self):
        data = {'name': 'Cave of Doom'}
        self._test_patch_public_spatial_unit(data, 404,
                                             su=SpatialUnitFactory.create(),
                                             non_existent=True,
                                             no_change=True)

    def test_update_with_invalid_data(self):
        data = {'name': ''}
        self._test_patch_public_spatial_unit(data, 400,
                                             no_change=True,
                                             field_error='name')

    def test_update_with_invalid_geometry(self):
        data = {
            'geometry': {
                'type': 'Cats',
                'coordinates': [100, 0]
            }
        }
        self._test_patch_public_spatial_unit(data, 400,
                                             no_change=True,
                                             field_error='geometry')

    def test_update_with_unauthorized_user(self):
        data = {'name': 'Anonymous Location'}
        self._test_patch_public_spatial_unit(data, 403, user=AnonymousUser(),
                                             check_error=True,
                                             no_change=True)

    def test_update_private_spatial_unit(self):
        data = {'name': 'Private Spatial Unit'}
        self._test_patch_private_spatial_unit(data, status=200, check_ok=True)

    def test_update_private_spatial_unit_with_unauthroized_user(self):
        data = {'name': 'Anonymous Location'}
        self._test_patch_private_spatial_unit(data, user=AnonymousUser(),
                                              status=403, check_error=True,
                                              no_change=True)

    def test_update_private_spatial_unit_without_permission(self):
        data = {'name': 'Restricted Keep Out'}
        self._test_patch_private_spatial_unit(data, user=self.restricted_user,
                                              status=403, check_error=True,
                                              no_change=True)

    def test_update_private_spatial_unit_based_on_org_membership(self):
        data = {'name': 'Way Cooler Name'}
        self._test_patch_private_spatial_unit(data, user=UserFactory.create(),
                                              status=403, check_error=True,
                                              make_org_member=True,
                                              no_change=True)

    def test_update_private_spatial_unit_based_on_org_admin(self):
        data = {'name': 'Way Cooler Name'}
        self._test_patch_private_spatial_unit(data, user=UserFactory.create(),
                                              status=200, check_ok=True,
                                              make_org_admin=True)

    def test_update_private_spatial_unit_with_other_org_membership(self):
        data = {'name': 'I do not belong here'}
        self._test_patch_private_spatial_unit(data,  user=UserFactory.create(),
                                              status=403, check_error=True,
                                              make_other_org_member=True,
                                              no_change=True)


class SpatialUnitDeleteAPITest(SpatialUnitDetailTestCase):
    def _test_delete_public_spatial_unit(self, status, user=None,
                                         org='namati', prj='test-project',
                                         su=None, check_ok=False,
                                         check_error=False,
                                         non_existent=False):
        valid_su = self._test_objs()[0]
        su = su or valid_su
        if user is None:
            user = self.user
        content = self._delete(org=org, prj=prj, su=su, user=user,
                               status=status)
        if check_ok:
            self._get(org='namati', prj='test-project',
                      su=valid_su.id, status=404)
        if check_error:
            assert content['detail'] == PermissionDenied.default_detail
            self._get(org='namati', prj='test-project',
                      su=valid_su.id, status=200)
        if non_existent:
            if su != valid_su:
                assert content['detail'] == _("SpatialUnit not found.")
            else:
                assert content['detail'] == _("Project not found.")

    def _test_delete_private_spatial_unit(self, status=None, user=None,
                                          check_ok=False, check_error=False,
                                          make_org_member=False,
                                          make_org_admin=False,
                                          make_other_org_member=False):
        if user is None:
            user = self.user
        su, org = self._test_objs(access='private')
        if make_org_member:
            OrganizationRole.objects.create(organization=org, user=user)
        if make_org_admin:
            OrganizationRole.objects.create(organization=org, user=user,
                                            admin=True)
        if make_other_org_member:
            other_org = OrganizationFactory.create()
            OrganizationRole.objects.create(organization=other_org, user=user)
        content = self._delete(org='namati', prj='test-project', su=su,
                               user=user, status=status)
        if check_ok:
            self._get(org='namati', prj='test-project',
                      su=su.id, status=404)
        if check_error:
            assert content['detail'] == PermissionDenied.default_detail
            self._get(org='namati', prj='test-project',
                      su=su.id, status=200)

    def test_delete_spatial_unit(self):
        self._test_delete_public_spatial_unit(status=204, check_ok=True)

    def test_delete_with_nonexistent_org(self):
        self._test_delete_public_spatial_unit(status=404, org='evil-corp',
                                              non_existent=True)

    def test_delete_with_nonexistent_project(self):
        self._test_delete_public_spatial_unit(status=404, prj='world-dom',
                                              non_existent=True)

    def test_delete_with_nonexistent_spatial_unit(self):
        self._test_delete_public_spatial_unit(status=404,
                                              su=SpatialUnitFactory.create(),
                                              non_existent=True)

    def test_delete_with_unauthorized_user(self):
        self._test_delete_public_spatial_unit(status=403, user=AnonymousUser(),
                                              check_error=True)

    def test_delete_private_spatial_unit(self):
        self._test_delete_private_spatial_unit(status=204, check_ok=True)

    def test_delete_private_spatial_unit_with_unauthroized_user(self):
        self._test_delete_private_spatial_unit(user=AnonymousUser(),
                                               status=403, check_error=True)

    def test_delete_private_spatial_unit_without_permission(self):
        self._test_delete_private_spatial_unit(user=self.restricted_user,
                                               status=403, check_error=True)

    def test_delete_private_spatial_unit_based_on_org_membership(self):
        self._test_delete_private_spatial_unit(user=UserFactory.create(),
                                               status=403, check_error=True,
                                               make_org_member=True)

    def test_delete_private_spatial_unit_based_on_org_admin(self):
        self._test_delete_private_spatial_unit(user=UserFactory.create(),
                                               status=204, check_ok=True,
                                               make_org_admin=True)

    def test_delete_private_spatial_unit_with_other_org_membership(self):
        self._test_delete_private_spatial_unit(user=UserFactory.create(),
                                               status=403, check_error=True,
                                               make_other_org_member=True)
