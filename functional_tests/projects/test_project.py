# from base import FunctionalTest
# from fixtures import load_test_data
# from fixtures.common_test_data_2 import get_test_data
# from django.contrib.gis.geos import GEOSGeometry

# from core.tests.factories import PolicyFactory
# from organization.models import OrganizationRole
# from accounts.tests.factories import UserFactory
# from resources.tests.factories import ResourceFactory
# from spatial.tests.factories import SpatialUnitFactory
# from party.tests.factories import PartyFactory, TenureRelationshipFactory
# from party.models import TenureRelationshipType

# from pages.Login import LoginPage
# from pages.Project import ProjectPage


# class ProjectTest(FunctionalTest):
#     def setUp(self):
#         super().setUp()
#         PolicyFactory.load_policies()
#         test_objs = load_test_data(get_test_data())
#         self.org = test_objs['organizations'][0]
#         self.prj = test_objs['projects'][1]
#         OrganizationRole.objects.create(
#                 organization=self.org,
#                 user=UserFactory.create(
#                         username='admin_user',
#                         password='password'),
#                 admin=True)
#         ResourceFactory.create_batch(
#             2, content_object=self.prj,
#             project=self.prj)
#         su = SpatialUnitFactory(
#             geometry=GEOSGeometry('{"type": "Polygon",'
#                                   '"coordinates": [['
#                                   '[-5.1031494140625000,'
#                                   ' 8.1299292850467957], '
#                                   '[-5.0482177734375000, '
#                                   '7.6837733211111425], '
#                                   '[-4.6746826171875000, '
#                                   '7.8252894725496338], '
#                                   '[-4.8641967773437491, '
#                                   '8.2278005261522775], '
#                                   '[-5.1031494140625000, '
#                                   '8.1299292850467957]]]}'),
#             project=self.prj,
#             type='MI',
#             attributes={})
#         ResourceFactory.create(
#             content_object=su,
#             project=self.prj)
#         party = PartyFactory.create(project=test_objs['projects'][1])
#         tenure = TenureRelationshipFactory.create(
#             project=self.prj,
#             party=party,
#             spatial_unit=su,
#             tenure_type=TenureRelationshipType.objects.create(
#                 id='CR',
#                 label='Customary Rights'))
#         ResourceFactory.create(
#             content_object=su,
#             project=self.prj)
#         ResourceFactory.create(
#             content_object=party,
#             project=self.prj)
#         ResourceFactory.create(
#             content_object=tenure,
#             project=self.prj)

#     def test_project_archived_view(self):
#         LoginPage(self).login('admin_user', 'password')
#         page = ProjectPage(self, self.org.slug, self.prj.slug)
#         page.go_to()
#         self.get_screenshot('project page')
#         assert 'ARCHIVED' in page.get_project_name()

#         # Test main dashboard page
#         page.click_on_add_location_button(success=False)
#         page.click_on_add_resource_button_from_dropdown(success=False)
#         page.click_on_edit_boundary_button('geometry', success=False)
#         page.click_on_edit_boundary_button('details', success=False)
#         page.click_on_edit_boundary_button('permissions', success=False)

#         # Test spatial unit
#         page.click_on_location()
#         page.click_on_edit_button(success=False)
#         page.click_on_delete_button(success=False)

#         # Test spatial unit resource tab
#         page.click_on_location_resource_tab()
#         page.click_on_add_button('active', success=False)
#         page.click_on_location_resource_tab()
#         page.click_on_detach_resource_button('detail', success=False)

#         # Test spatial unit relationship tab
#         page.click_on_location_relationship_tab()
#         page.click_on_add_button('active', success=False)
#         page.click_on_location_relationship_tab()

#         # Test spatial unit relationship tab
#         page.click_on_relationship_in_table()
#         page.click_on_edit_button(success=False)
#         page.click_on_delete_button(success=False)
#         page.click_on_add_button('detail', success=False)
#         page.click_on_detach_resource_button('detail', success=False)

#         # Test party page
#         page.click_on_party_in_table()
#         page.click_on_edit_button(success=False)
#         page.click_on_delete_button(success=False)
#         page.click_on_add_button('panel-body', success=False)
#         page.click_on_detach_resource_button('panel-body', success=False)

#         # Test project resource page
#         page.click_on_resources_tab()
#         page.click_on_add_button('panel-body', success=False)
#         page.click_on_detach_resource_button('panel-body', success=False)

#         page.click_on_resource_in_table()
#         page.click_on_edit_resource_button(success=False)
#         page.click_on_delete_resource_button_and_confirm(success=False)
